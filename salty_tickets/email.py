# from salty_tickets import app
import logging
import requests
from flask import render_template
from salty_tickets import config
from premailer import transform, Premailer
from salty_tickets.config import EMAIL_FROM
from salty_tickets.controllers import OrderSummaryController, OrderProductController


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

    body_html = render_template('email/registration_confirmation.html', order_summary_controller=order_summary_controller)
    body_html = prepare_email_html(body_html)

    body_text = render_template('email/registration_confirmation.txt', order_summary_controller=order_summary_controller)

    subj = '{} - Registration'.format(user_order.event.name)

    send_email(EMAIL_FROM, user_order.registration.email, subj, body_text, body_html)


def send_acceptance_from_waiting_list(order_product):
    order_product_controller = OrderProductController(order_product)

    body_html = render_template('email/acceptance_from_waiting_list.html', order_product_controller=order_product_controller)
    body_html = prepare_email_html(body_html)

    body_text = render_template('email/acceptance_from_waiting_list.txt', order_product_controller=order_product_controller)

    subj = '{} - {} - You are in!'.format(order_product.order.event.name, order_product.name)

    send_email(EMAIL_FROM, order_product.registrations[0].email, subj, body_text, body_html)
