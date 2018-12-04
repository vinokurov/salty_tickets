import logging

import requests
from flask import render_template, url_for
from premailer import Premailer
from salty_tickets import config
from salty_tickets.config import EMAIL_FROM
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.registrations import Payment, Registration
from salty_tickets.tokens import PaymentId, PartnerToken


def send_email(email_from, email_to, subj, body_text, body_html, files=None):
    email_data = {
        'from': email_from,
        'to': [email_to],
        'subject': subj,
        'text': body_text,
        'html': body_html
    }
    if not config.MODE_TESTING:
        email_data['bcc'] = config.EMAIL_DEBUG
    result = requests.post('https://api.mailgun.net/v3/saltyjitterbugs.co.uk/messages',
                           auth=('api', config.MAILGUN_KEY),
                           data=email_data,
                           files=files)
    return result


def send_registration_confirmation(payment: Payment, event: Event):
    order_status_url = url_for('user_order_index', pmt_token=PaymentId().serialize(payment), _external=True)

    # ptn_token = PartnerToken().serialize(payment.paid_by)
    body_text = render_template('email/registration_confirmation.txt',
                                payment=payment,
                                event=event,
                                # ptn_token=ptn_token,
                                order_status_url=order_status_url)

    subj = f'{event.name} - Registration'

    return send_email(EMAIL_FROM, payment.paid_by.email, subj, body_text, body_html=None)


def send_waiting_list_accept_email(dao: TicketsDAO, registration: Registration):
    payment = dao.get_payment_by_registration(registration)
    event = dao.get_payment_event(payment)
    order_status_url = url_for('user_order_index', pmt_token=PaymentId().serialize(payment), _external=True)
    body_text = render_template('email/acceptance_from_waiting_list.txt',
                                registration=registration,
                                event=event,
                                order_status_url=order_status_url)

    subj = f'{event.name} - You are in!'

    return send_email(EMAIL_FROM, registration.person.email, subj, body_text, body_html=None)


##############################################################################################
##############################################################################################
##############################################################################################

def prepare_email_html(html):
    pr = Premailer(html, cssutils_logging_level=logging.CRITICAL)
    html_for_email = pr.transform()
    import re
    html_for_email = re.sub(r'<style.*</style>', '', html_for_email, flags=re.DOTALL)
    # print(html_for_email)
    return html_for_email


def pdf_attachment_from_url(url, filename):
    import weasyprint
    pdf = weasyprint.HTML(url)
    attachment = ("attachment", (filename, pdf.write_pdf()))
    return attachment

