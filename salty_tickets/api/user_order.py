from typing import List, Dict

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.discounts import DiscountProduct
from salty_tickets.models.event import Event
from salty_tickets.models.products import Product
from salty_tickets.models.tickets import Ticket, WorkshopTicket
from salty_tickets.models.registrations import Payment, Registration, Purchase, Discount
from salty_tickets.tokens import PartnerToken, PaymentId


@dataclass
class RegistrationInfo(DataClassJsonMixin):
    title: str
    start_datetime: str = ''
    end_datetime: str = ''
    level: str = None
    teachers: str = None
    price: float = None
    is_paid: bool = False
    paid_price: float = None
    info: str = None
    wait_listed: bool = False
    person: str = None
    partner: str = None
    dance_role: str = None
    ticket_class: str = None

    @classmethod
    def from_registration(cls, registration: Registration, event_products: Dict[str, Ticket]):
        product = event_products[registration.ticket_key]
        kwargs = dict(
            person=registration.person.full_name,
            title=product.name,
            info=product.info,
            price=registration.price,
            # paid_price=registration.paid_price,
            is_paid=registration.is_paid,
            wait_listed=registration.wait_listed,
            ticket_class=product.__class__.__name__
        )
        if registration.partner:
            kwargs['partner'] = registration.partner.full_name

        if isinstance(product, WorkshopTicket):
            kwargs.update(dict(
                start_datetime=str(product.start_datetime),
                end_datetime=str(product.end_datetime),
                level=product.level,
                teachers=product.teachers,
                dance_role=registration.dance_role,
            ))

        return cls(**kwargs)


@dataclass
class DiscountInfo(DataClassJsonMixin):
    person: str
    price: float = None
    info: str = None

    @classmethod
    def from_discount(cls, discount: Discount, event_discounts: Dict[str, DiscountProduct]):
        kwargs = dict(
            info=discount.description,
            price=discount.value,
            person=discount.person.full_name
        )
        return cls(**kwargs)


@dataclass
class PurchaseInfo(DataClassJsonMixin):
    title: str
    price: float = None
    amount: int = 0
    is_paid: bool = False
    info: str = None

    @classmethod
    def from_purchase(cls, purchase: Purchase, event_products: Dict[str, Product]):
        product = event_products[purchase.product_key]
        kwargs = dict(
            title=f'{product.name} / {product.options[purchase.product_option_key]}',
            amount=purchase.amount,
            info=product.info,
            price=purchase.price,
            # paid_price=registration.paid_price,
            is_paid=purchase.is_paid,
        )
        return cls(**kwargs)


@dataclass
class UserOrderInfo(DataClassJsonMixin):
    name: str
    email: str
    ptn_token: str = None
    pmt_token: str = None
    event_name: str = None
    event_info: str = None
    price: float = None
    paid_price: float = None
    tickets: List[RegistrationInfo] = field(default_factory=list)
    products: List[PurchaseInfo] = field(default_factory=list)
    discounts: List[DiscountInfo] = field(default_factory=list)

    @classmethod
    def from_payment(cls, payment: Payment, event: Event):
        return cls(
            name=payment.paid_by.full_name,
            email=payment.paid_by.email,
            ptn_token=PartnerToken().serialize(payment.paid_by),
            pmt_token=PaymentId().serialize(payment),
            tickets=[RegistrationInfo.from_registration(r, event.tickets) for r in payment.registrations],
            products=[PurchaseInfo.from_purchase(r, event.products) for r in payment.purchases],
            discounts=[DiscountInfo.from_discount(r, event.discount_products) for r in payment.discounts],
            event_name=event.name,
            event_info=event.info,
            price=payment.price,
            paid_price=payment.paid_price,
        )


def do_get_user_order_info(dao: TicketsDAO, pmt_token: str):
    payment = PaymentId().deserialize(dao, pmt_token)
    event = dao.get_payment_event(payment, get_registrations=False)
    return UserOrderInfo.from_payment(payment, event)
