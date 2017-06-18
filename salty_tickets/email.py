# from salty_tickets import app
import requests
from flask import render_template
from salty_tickets import config
from premailer import transform


def send_email(email_from, email_to, subj, body, body_html):
    result = requests.post('https://api.mailgun.net/v3/saltyjitterbugs.co.uk/messages',
                           auth=('api', config.MAILGUN_KEY),
                           data={
                               'from': email_from,
                               'to': [email_to],
                               'subject': subj,
                               'text': body,
                               'html': body_html
                           })

def confirmation_email():
    html = render_template('signup_thankyou.html', event_key='salty_recipes_with_pol_sara', app=app)
    html_for_email = transform(html)
    send_email(config.EMAIL_FROM, 'alexander.a.vinokurov@gmail.com', 'Registration successful', 'text body', html_for_email)
