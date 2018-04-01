from salty_tickets.config import EMAIL_FROM
from salty_tickets.emails import send_email, pdf_attachment_from_url


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

email_to = 'alexander.a.vinokurov@gmail.com'
email_subject = 'Mind the Shag - Your Ticket'
email_text = 'Testing PDF'
email_html = 'Testing PDF'
url = 'https://www.saltyjitterbugs.co.uk/register/order/Mjgx.A0c5r7wR1PExzPjQmuQdJWbFCR8'
attachment = pdf_attachment_from_url(url, 'Mind the Shag - Ticket.pdf')
res = send_email(EMAIL_FROM, email_to, email_subject, email_text, email_html, [attachment])