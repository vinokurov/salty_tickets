from salty_tickets.config import EMAIL_FROM, MODE_TESTING
from salty_tickets.emails import send_email, pdf_attachment_from_url
from salty_tickets.models import Order, Registration, OrderProduct
from salty_tickets.mts_controllers import MtsTicketController

# import weasyprint
# import requests

# data = {
#     'from':'Salty Jitterbugs <registration@saltyjitterbugs.co.uk>',
#     'to':'alexander.a.vinokurov@gmail.com',
#     'subject':'test pdf',
#     'text':'Test pdf'
# }
#
# pdf=weasyprint.HTML('https://www.saltyjitterbugs.co.uk/register/order/Mjgx.A0c5r7wR1PExzPjQmuQdJWbFCR8')
# pdf_bytes = pdf.write_pdf()
# attachment = ("attachment", ('test.pdf', pdf_bytes))
# r = requests.post('https://api.mailgun.net/v3/saltyjitterbugs.co.uk/messages',
#                   auth=('api', 'key-f2f231b6c20ab438aedd7a2f3b919e84'), data=data, files=[attachment])

MODE_TESTING = True

email_subject = 'Mind the Shag - Your Ticket'
email_text = """Dear traveler,

Mind the Shag is just around the corner! Please find your tickets attached.
At the registration desk please prepare a printed version of the tickets or just show them on the phone.

Best
Mind the Shag Team"""

for user_order in Order.query.filter_by(event_id=6, status='paid').filter(Order.id>121).limit(10).all():
    # email_to = user_order.registration.email
    email_to = 'alexander.a.vinokurov@gmail.com'

    attachments = []
    for registration in Registration.query.join(OrderProduct, aliased=True).filter_by(order_id=user_order.id).distinct():
        ticket_controller = MtsTicketController(registration)
        url = f'https://www.saltyjitterbugs.co.uk/mts/{ticket_controller.token}'
        print(user_order.id, registration.id, url)
        attachments.append(pdf_attachment_from_url(url, f'Mind the Shag Ticket - {registration.name}.pdf'))

    res = send_email(EMAIL_FROM, email_to, email_subject, email_text, None, attachments)
    print(user_order.id, user_order.registration.name, len(attachments))

#email_to = 'alexander.a.vinokurov@gmail.com'
#email_subject = 'Mind the Shag - Your Ticket'
#email_text = 'Testing PDF'
#email_html = 'Testing PDF'
#url = 'https://www.saltyjitterbugs.co.uk/register/order/Mjgx.A0c5r7wR1PExzPjQmuQdJWbFCR8'
#attachment = pdf_attachment_from_url(url, 'Mind the Shag - Ticket.pdf')
#res = send_email(EMAIL_FROM, email_to, email_subject, email_text, email_html, [attachment])