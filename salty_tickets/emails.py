import logging

import requests
import typing
from flask import render_template, url_for
from premailer import Premailer
from salty_tickets import config
from salty_tickets.config import EMAIL_FROM
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.registrations import Payment, Registration
from salty_tickets.tokens import PaymentId, PartnerToken, RegistrationToken


def send_email(email_from: str, email_to: str, subj: str, body_text: str, body_html: str, files: typing.List=None):
    email_data = {
        'from': email_from,
        'to': [email_to],
        'subject': subj,
        'text': body_text,
        'html': body_html
    }
    if not config.MODE_TESTING:
        email_data['bcc'] = config.EMAIL_DEBUG
    logging.info(email_data)
    result = requests.post('https://api.mailgun.net/v3/saltyjitterbugs.co.uk/messages',
                           auth=('api', config.MAILGUN_KEY),
                           data=email_data,
                           files=files)
    return result


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

