import reachmail
import json

from salty_tickets import config


def getAccountGuid(api):
    res = api.adminsitration.users_current()
    if res[0] == 200 :
        data=json.loads(res[1]) #parse json response
        return data['AccountId']
    else:
        print("Oops. Could not find your Account Guid. \nStatus Code: %s \nResponse: %s" % (res[0], res[1]))
        exit(1)

#this functions builds the body of the message and returns the response after checking the connection
def sendEmail(to_address, subject, body):
    api = reachmail.ReachMail(config.REACHMAIL_TOKEN)
    AccountId = getAccountGuid(api)

    email_body={
    'FromAddress': 'salty.jitterbugs@gmail.com',
    'Recipients': [
    {
        'Address': to_address
        },
    ],
    'Subject': subject ,
    'Headers': {
        'From': 'Salty Jitterbugs <salty.jitterbugs@gmail.com>',
        'X-Company': 'Salty Jitterbugs',
        'X-Location': 'London'
    },
    'BodyText': body,
    'BodyHtml': body,
    'Tracking': 'true'
    }
    send = api.easysmtp.delivery(AccountId=AccountId, Data=email_body)
    if send[0] == 200:
        return send[1]
    else:
        print("Could not Deliver message.  \nStatus Code: %s \nResponse: %s" % (send[0], send[1]))
