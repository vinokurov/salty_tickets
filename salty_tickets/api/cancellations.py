import typing

from salty_tickets import TicketsDAO
from salty_tickets.api.event_utils import get_event_active_registrations
from salty_tickets.api.registration_process import balance_event_waiting_lists
from salty_tickets.constants import SUCCESSFUL
from salty_tickets.models.event import Event
from salty_tickets.models.registrations import Payment, Registration, TransactionDetails
from salty_tickets.tasks import update_event_numbers


def cancel_registration(dao: TicketsDAO, registration: Registration) -> None:
    registration.active = False
    dao.update_registration(registration)


def get_registrations_by_email(dao: TicketsDAO, event: Event, email: str) -> typing.List[Registration]:
    registrations = get_event_active_registrations(dao, event)
    return [reg for reg in registrations if reg.person.email == email]


def add_refund_payment(dao: TicketsDAO, event_key: str, payer_email: str, amount: float):
    event = dao.get_event_by_key(event_key)
    payments = dao.get_payments_by_event(event)
    payers = [pmt.paid_by for pmt in payments if pmt.status == SUCCESSFUL and pmt.paid_by.email == payer_email]
    if not payers:
        return

    payer = payers[0]
    refund_payment = Payment(
        paid_by=payer,
        price=-amount,
        description='Refund',
        status=SUCCESSFUL,
        transactions=[TransactionDetails(
            price=-amount,
            description='Refund',
            success=True,
        )],
    )
    dao.add_payment(refund_payment, event)


def cancel_all_for_email(dao: TicketsDAO, event_key: str, email: str):
    event = dao.get_event_by_key(event_key)
    registrations = get_registrations_by_email(dao, event, email)
    for reg in registrations:
        cancel_registration(dao, reg)
    update_event_numbers(dao, event)
    balance_event_waiting_lists(dao, event.key)