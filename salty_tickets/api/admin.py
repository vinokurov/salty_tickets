from typing import List, Dict, Optional

from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from salty_tickets.api.registration_process import ProductWaitingListInfo
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct
from salty_tickets.models.registrations import ProductRegistration, Payment
from salty_tickets.tokens import PaymentId, PartnerToken


@dataclass
class RegistrationInfo(DataClassJsonMixin):
    id: str
    name: str
    email: str
    product: str
    price: float
    paid_price: float
    wait_listed: bool
    active: bool
    payment_id: str
    payment_token: str
    dance_role: str = None
    partner: str = None
    ptn_token: str = None

    @classmethod
    def from_registration(cls, dao: TicketsDAO, registration: ProductRegistration, event: Event):
        payment = dao.get_payment_by_registration(registration)
        if registration.partner:
            partner = registration.partner.full_name
        else:
            partner = None
        return cls(
            id=str(registration.id),
            name=registration.person.full_name,
            email=registration.person.email,
            product=event.products[registration.product_key].name,
            price=registration.price,
            paid_price=registration.paid_price,
            wait_listed=registration.wait_listed,
            active=registration.active,
            dance_role=registration.dance_role,
            partner=partner,
            payment_id=str(payment.id),
            payment_token=PaymentId().serialize(payment),
            ptn_token=PartnerToken().serialize(registration.person),
        )


@dataclass
class PaymentInfo(DataClassJsonMixin):
    id: str
    pmt_token: str
    name: str
    email: str
    price: float
    paid_price: float
    status: str
    stripe: Dict

    @classmethod
    def from_payment(cls, payment: Payment):
        return cls(
            id=str(payment.id),
            pmt_token=PaymentId().serialize(payment),
            name=payment.paid_by.full_name,
            email=payment.paid_by.email,
            price=payment.price,
            paid_price=payment.paid_price,
            status=payment.status,
            stripe=payment.stripe,
        )


@dataclass
class ProductInfo(DataClassJsonMixin):
    key: str
    title: str
    start_datetime: str
    end_datetime: str
    time: str = None
    level: str = None
    teachers: str = None
    available: int = None
    price: float = None
    info: str = None
    waiting_list: Optional[ProductWaitingListInfo] = None
    ratio: float = None

    @classmethod
    def from_workshop(cls, workshop: WorkshopProduct):
        available = workshop.max_available - workshop.waiting_list.total_accepted
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
            waiting_list=ProductWaitingListInfo(**workshop.waiting_list.waiting_stats)
        )





@dataclass
class EventInfo(DataClassJsonMixin):
    name: str
    key: str
    products: List[ProductInfo]
    layout: Dict
    registrations: List[RegistrationInfo]
    payments: List[PaymentInfo]

    @classmethod
    def from_event(cls, dao: TicketsDAO, event: Event):
        registrations = dao.query_registrations(event=event)
        payments = dao.get_payments_by_event(event)
        return cls(
            name=event.name,
            key=event.key,
            products=[ProductInfo.from_workshop(p) for k, p in event.products.items()
                      if isinstance(p, WorkshopProduct)],
            layout=event.layout,
            registrations=[RegistrationInfo.from_registration(dao, r, event) for r in registrations],
            payments=[PaymentInfo.from_payment(p) for p in payments]
        )


def do_get_event_stats(dao: TicketsDAO, event_key: str):
    event = dao.get_event_by_key(event_key)
    return EventInfo.from_event(dao, event)
