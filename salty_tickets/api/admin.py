from typing import List, Dict, Optional

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from salty_tickets.api.registration_process import TicketWaitingListInfo
from salty_tickets.constants import LEADER, FOLLOWER, SUCCESSFUL
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.tickets import WorkshopTicket
from salty_tickets.models.registrations import Registration, Payment
from salty_tickets.tokens import PaymentId, PartnerToken


@dataclass
class SummaryInfo(DataClassJsonMixin):
    persons_count: int
    workshops_accepted: int
    workshops_wait_listed: int
    total_sales: float
    amount_paid: float
    amount_due_later: float

    @classmethod
    def from_event(cls, event: Event, payments: List[Payment]):
        registrations = []
        for p_key, p in event.tickets.items():
            registrations = registrations + p.registrations
        registrations = [r for r in registrations if r.active]

        total_sales = sum([p.price for p in payments if p.price and p.status == SUCCESSFUL] or [0])
        amount_paid = sum([p.paid_price for p in payments if p.price and p.status == SUCCESSFUL] or [0])
        # amount_paid = sum([r.paid_price for r in registrations if r.paid_price] or [0])
        return cls(
            persons_count=len(set([r.person.full_name for r in registrations])),
            workshops_accepted=len([r for r in registrations if not r.wait_listed
                                    and isinstance(event.tickets[r.ticket_key], WorkshopTicket)]),
            workshops_wait_listed=len([r for r in registrations if r.wait_listed]),
            total_sales=total_sales,
            amount_paid=amount_paid,
            amount_due_later=total_sales - amount_paid
        )


@dataclass
class RegistrationInfo(DataClassJsonMixin):
    id: str
    name: str
    email: str
    ticket: str
    ticket_key: str
    price: float
    # paid_price: float
    is_paid: bool
    wait_listed: bool
    active: bool
    dance_role: str = None
    partner: str = None
    ptn_token: str = None

    @classmethod
    def from_registration(cls, registration: Registration, event: Event):
        if registration.partner:
            partner = registration.partner.full_name
        else:
            partner = None
        return cls(
            id=str(registration.id),
            name=registration.person.full_name,
            email=registration.person.email,
            ticket=event.tickets[registration.ticket_key].name,
            ticket_key=registration.ticket_key,
            price=registration.price,
            # paid_price=registration.paid_price,
            is_paid=registration.is_paid,
            wait_listed=registration.wait_listed,
            active=registration.active,
            dance_role=registration.dance_role,
            partner=partner,
            # ptn_token=PartnerToken().serialize(registration.person),
        )


@dataclass
class PaymentInfo(DataClassJsonMixin):
    id: str
    # pmt_token: str
    name: str
    email: str
    price: float
    paid_price: float
    status: str
    stripe: Dict
    partner: str = None

    @classmethod
    def from_payment(cls, payment: Payment):
        regs = [r.partner for r in payment.registrations if r.partner and r.partner != r.registered_by]
        if regs:
            partner = regs[0].full_name
        else:
            partner = None
        return cls(
            id=str(payment.id),
            # pmt_token=PaymentId().serialize(payment),
            name=payment.paid_by.full_name,
            email=payment.paid_by.email,
            price=payment.price,
            paid_price=payment.paid_price,
            status=payment.status,
            stripe=payment.stripe,
            partner=partner,
        )


@dataclass
class ProductInfo(DataClassJsonMixin):
    key: str
    title: str
    start_datetime: str
    end_datetime: str
    registrations: List[RegistrationInfo]
    time: str = None
    level: str = None
    teachers: str = None
    available: int = None
    price: float = None
    info: str = None
    waiting_list: Optional[TicketWaitingListInfo] = None
    ratio: float = None
    leaders: str = None
    followers: str = None
    current_ratio: float = None
    has_wait_list: bool = False

    @classmethod
    def from_workshop(cls, event, workshop: WorkshopTicket):
        available = workshop.max_available - workshop.waiting_list.total_accepted

        def _role_stat(role):
            stat = str(workshop.waiting_list.registration_stats[role].accepted)
            if workshop.waiting_list.registration_stats[role].waiting:
                stat = stat + ' + ' + str(workshop.waiting_list.registration_stats[role].waiting)
            return stat

        return cls(
            key=workshop.key,
            title=workshop.name,
            start_datetime=str(workshop.start_datetime),
            end_datetime=str(workshop.end_datetime),
            level=workshop.level,
            teachers=workshop.teachers,
            available=available,
            price=workshop.base_price,
            info=workshop.info,
            waiting_list=TicketWaitingListInfo(**workshop.waiting_list.waiting_stats),
            registrations=[RegistrationInfo.from_registration(r, event) for r in workshop.registrations],
            leaders=_role_stat(LEADER),
            followers=_role_stat(FOLLOWER),
            current_ratio=workshop.waiting_list.current_ratio,
            has_wait_list=workshop.waiting_list.has_waiting_list,
            ratio=workshop.ratio,
        )


@dataclass
class EventInfo(DataClassJsonMixin):
    name: str
    key: str
    products: List[ProductInfo]
    layout: Dict
    payments: List[PaymentInfo]
    summary: SummaryInfo

    @classmethod
    def from_event(cls, dao: TicketsDAO, event: Event):
        # registrations = dao.query_registrations(event=event)
        payments = dao.get_payments_by_event(event)
        return cls(
            name=event.name,
            key=event.key,
            products=[ProductInfo.from_workshop(event, p) for k, p in event.tickets.items()
                      if isinstance(p, WorkshopTicket)],
            layout=event.layout,
            payments=[PaymentInfo.from_payment(p) for p in payments],
            summary=SummaryInfo.from_event(event, payments)
        )


def do_get_event_stats(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key)
    return EventInfo.from_event(dao, event)
