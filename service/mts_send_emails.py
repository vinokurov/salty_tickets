import unidecode
from salty_tickets import config
from salty_tickets.emails import send_email, pdf_attachment_from_url
from salty_tickets.models import Order, Registration, OrderProduct
from salty_tickets.mts_controllers import MtsTicketController

config.MODE_TESTING = True

email_subject = 'Mind the Shag - Your Ticket'
email_text = """Dear traveler,

Mind the Shag is just around the corner! Please find your tickets attached.
At the registration desk please have prepared an electronic or printed version of the tickets.
If you notice anything that looks incorrect in your tickets, please do contact us!

See you soon!
Mind the Shag Team"""

#for user_order in Order.query.filter_by(event_id=6, status='paid').all():
for user_order in Order.query.filter_by(event_id=6, status='paid').filter(Order.id==220).all():
    email_to = user_order.registration.email
    #email_to_salty = 'salty.jitterbugs@gmail.com'
    #email_to = 'alexander.a.vinokurov@gmail.com'

    #if 'hotmail' not in user_order.registration.email:
    #    continue

    attachments = []
    for registration in Registration.query.join(OrderProduct, aliased=True).filter_by(order_id=user_order.id).distinct():
        ticket_controller = MtsTicketController(registration)
        url = f'https://www.saltyjitterbugs.co.uk/mts/{ticket_controller.token}'
        reg_name = unidecode.unidecode(registration.name)
        attachments.append(pdf_attachment_from_url(url, f'Mind the Shag Ticket - {reg_name}.pdf'))

    res = send_email(config.EMAIL_FROM, email_to, email_subject, email_text, None, attachments)
    #res=''
    print(user_order.id, user_order.registration.name, email_to, len(attachments), res)

