from salty_tickets.api.registration_process import set_payment_totals
from salty_tickets.config import MONGO
from salty_tickets.constants import LEADER, SUCCESSFUL
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.registrations import Payment, Registration

dao = TicketsDAO(host=MONGO)
event = dao.get_event_by_key('mind_the_shag_2019')
person = dao.get_person_by_id("5c110cbbb01bad00409a4d42")

registrations = [Registration(
        person=person,
        registered_by=person,
        ticket_key='shag_clinic',
        dance_role=LEADER,
        price=0,
        paid_price=0,
        is_paid=True,
        active=True
    )]

payment = Payment(
    paid_by=person,
    registrations=registrations,
    status=SUCCESSFUL,
    info_items=[(event.tickets[r.ticket_key].item_info(r), r.price) for r in registrations],
    pay_all_now=True,
)
set_payment_totals(payment)

import pdb;pdb.set_trace()
dao.add_payment(payment, event, register=True)

