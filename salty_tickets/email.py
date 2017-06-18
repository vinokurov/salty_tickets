# from salty_tickets import app
import logging
import requests
from flask import render_template
from salty_tickets import config
from premailer import transform, Premailer
from salty_tickets.config import EMAIL_FROM
from salty_tickets.controllers import OrderSummaryController


def send_email(email_from, email_to, subj, body_text, body_html):
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
                           data=email_data)


def prepare_email_html(html):
    pr = Premailer(html, cssutils_logging_level=logging.CRITICAL)
    html_for_email = pr.transform()
    import re
    html_for_email = re.sub(r'<style.*</style>', '', html_for_email, flags=re.DOTALL)
    # print(html_for_email)
    return html_for_email


def send_registration_confirmation(user_order):
    order_summary_controller = OrderSummaryController(user_order)

    html = render_template('email/registration_confirmation.html', order_summary_controller=order_summary_controller)
    html = prepare_email_html(html)

    # TODO: plain text email

    subj = '{} - Registration'.format(user_order.event.name)

    send_email(EMAIL_FROM, user_order.registration.email, subj, '', html)
