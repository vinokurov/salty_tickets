from typing import List, Dict

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.products import BaseProduct, WorkshopProduct
from salty_tickets.models.registrations import Payment, ProductRegistration
from salty_tickets.tokens import PartnerToken, PaymentId


@dataclass
class ProductRegistrationInfo(DataClassJsonMixin):
    title: str
    start_datetime: str
    end_datetime: str
    level: str = None
    teachers: str = None
    price: float = None
    paid_price: float = None
    info: str = None
    wait_listed: bool = False
    person: str = None
    partner: str = None
    dance_role: str = None

    @classmethod
    def from_registration(cls, registration: ProductRegistration, event_products: Dict[str, BaseProduct]):
        product = event_products[registration.product_key]
        kwargs = dict(
            person=registration.person.full_name,
            title=product.name,
            info=product.info,
            price=registration.price,
            paid_price=registration.paid_price,
            wait_listed=registration.wait_listed,
        )
        if registration.partner:
            kwargs['partner'] = registration.partner.full_name

        if isinstance(product, WorkshopProduct):
            kwargs.update(dict(
                start_datetime=str(product.start_datetime),
                end_datetime=str(product.end_datetime),
                level=product.level,
                teachers=product.teachers,
                dance_role=registration.dance_role,
            ))

        return cls(**kwargs)


@dataclass
class UserOrderInfo(DataClassJsonMixin):
    name: str
    email: str
    ptn_token: str = None
    pmt_token: str = None
    event_name: str = None
    event_info: str = None
    products: List[ProductRegistrationInfo] = field(default_factory=list)

    @classmethod
    def from_payment(cls, payment: Payment, event: Event):
        return cls(
            name=payment.paid_by.full_name,
            email=payment.paid_by.email,
            ptn_token=PartnerToken().serialize(payment.paid_by),
            pmt_token=PaymentId().serialize(payment),
            products=[ProductRegistrationInfo.from_registration(r, event.products)
                      for r in payment.registrations],
            event_name=event.name,
            event_info=event.info
        )


def do_get_user_order_info(dao: TicketsDAO, pmt_token: str):
    payment = PaymentId().deserialize(dao, pmt_token)
    event = dao.get_payment_event(payment, get_registrations=False)
    return UserOrderInfo.from_payment(payment, event)
