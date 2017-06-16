import requests
from salty_tickets import config


def send_email(email_from, email_to, subj, body):
    result = requests.post('https://api.mailgun.net/v3/saltyjitterbugs.co.uk/messages',
                           auth=('api', config.MAILGUN_KEY),
                           data={
                               'from': email_from,
                               'to': [email_to],
                               'subject': subj,
                               'text': body
                           })

