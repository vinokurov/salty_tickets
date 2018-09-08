import typing
from unittest import mock
from unittest.mock import Mock

import mongomock_mate # mongomock_mate import is required to run update() queries to mongomock
from datetime import datetime

import pytest
from dataclasses import dataclass
from flask import Flask as _Flask
from mongoengine import connect
from salty_tickets.constants import LEADER, FOLLOWER, SUCCESSFUL, FAILED
from salty_tickets.dao import EventDocument, RegistrationDocument, ProductRegistrationDocument, \
    PaymentDocument, TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct, PartyProduct, BaseProduct
from salty_tickets.models.registrations import PersonInfo
from salty_tickets.waiting_lists import flip_role
from stripe.error import CardError


class TestTicketsDAO(TicketsDAO):
    def __init__(self):
        db = connect(host='mongomock://localhost', db='salty_tickets')
        db.drop_database('salty_tickets')


@pytest.fixture
def test_dao():
    dao = TestTicketsDAO()
    return dao


@dataclass
class RegistrationMeta:
    product_key: str
    dance_role: str = None
    price: float = None
    name: str = None
    active: bool = None
    wait_listed: bool = False
    paid: float = None


@dataclass
class CoupleRegistrationMeta(RegistrationMeta):
    partner_name: str = None


@dataclass
class PaymentMeta:
    name: str
    registrations: typing.List[RegistrationMeta]
    status: str = SUCCESSFUL


@dataclass
class EventMeta:
    name: str
    info: str
    start_date: datetime
    end_date: datetime
    products: typing.List[BaseProduct]
    payments: typing.List[PaymentMeta]


@pytest.fixture
def salty_recipes(test_dao):
    event_meta = EventMeta(
        name='Salty Recipes',
        info='Salty Recipes Shag Weekender with super duper teachers',
        start_date=datetime(2018, 7, 10),
        end_date=datetime(2018, 7, 11),
        products=[
            WorkshopProduct(name='Saturday', base_price=25.0, max_available=15, ratio=1.2, allow_first=2, tags={'full'}),
            WorkshopProduct(name='Sunday', base_price=25.0, max_available=15, ratio=1.2, allow_first=2, tags={'full'}),
            PartyProduct('Party', base_price=10.0, max_available=50, tags={'full'}),
        ],
        payments=[
            PaymentMeta('Chang Schultheis', registrations=[
                RegistrationMeta('saturday', LEADER),
                RegistrationMeta('sunday', LEADER),
                RegistrationMeta('party'),
            ]),
            PaymentMeta('Brianna Mudd', registrations=[
                RegistrationMeta('saturday', FOLLOWER),
                RegistrationMeta('sunday', FOLLOWER),
                RegistrationMeta('party'),
            ]),
            PaymentMeta('Zora Dawe', [RegistrationMeta('saturday', FOLLOWER), RegistrationMeta('party')]),
            PaymentMeta('Sebrina Marler', [RegistrationMeta('saturday', FOLLOWER), RegistrationMeta('party')]),
            PaymentMeta('Yi Damon', [RegistrationMeta('saturday', FOLLOWER), RegistrationMeta('party')], FAILED),
            PaymentMeta('Yi Damon', [RegistrationMeta('saturday', FOLLOWER), RegistrationMeta('party')], SUCCESSFUL),
            PaymentMeta('Berta Sadowski', [
                RegistrationMeta('saturday', FOLLOWER, wait_listed=True),
                RegistrationMeta('party')
            ]),
            PaymentMeta('Emerson Damiano', [RegistrationMeta('sunday', LEADER), RegistrationMeta('party')]),
            PaymentMeta('Stevie Stumpf', [
                CoupleRegistrationMeta(product_key='sunday', dance_role=LEADER, partner_name='Albertine Segers'),
                RegistrationMeta('party'),
                RegistrationMeta('party', name='Albertine Segers'),
            ])
        ]
    )
    save_event_from_meta(event_meta)
    return event_meta


def save_event_from_meta(event_meta):
    new_event = EventDocument.from_dataclass(Event(
        name=event_meta.name,
        start_date=event_meta.start_date,
        end_date=event_meta.end_date,
        info=event_meta.info,
        products={p.key: p for p in event_meta.products}
    ))
    new_event.save(force_insert=True)

    event_meta.registration_docs = {}

    def _person_from_name(name):
        person_doc = RegistrationDocument(full_name=name, email=name.replace(' ', '.') + '@salty.co.uk')
        person_doc.save(force_insert=True)
        return person_doc

    persons = {}
    for payment in event_meta.payments:
        persons[payment.name] = _person_from_name(payment.name)
        for reg in payment.registrations:
            if reg.name and reg.name not in persons:
                persons[reg.name] = _person_from_name(reg.name)
            if isinstance(reg, CoupleRegistrationMeta) and reg.partner_name not in persons:
                persons[reg.partner_name] = _person_from_name(reg.partner_name)

    for payment_meta in event_meta.payments:
        registration_docs = []

        for reg_meta in payment_meta.registrations:
            price = reg_meta.price or new_event.products[reg_meta.product_key].base_price
            paid = reg_meta.paid or price

            if reg_meta.active is not None:
                active = reg_meta.active
            else:
                active = payment_meta.status == SUCCESSFUL

            if reg_meta.name is not None:
                reg = persons[reg_meta.name]
            else:
                reg = persons[payment_meta.name]

            kwargs = {'product_key': reg_meta.product_key, 'wait_listed': reg_meta.wait_listed,
                      'price': price, 'paid': paid,
                      'event': new_event, 'person': reg, 'registered_by': reg, 'active': active}
            if reg_meta.dance_role is not None:
                kwargs['dance_role'] = reg_meta.dance_role

            reg_doc = ProductRegistrationDocument(**kwargs)
            reg_doc.save(force_insert=True)
            registration_docs.append(reg_doc)

            if isinstance(reg_meta, CoupleRegistrationMeta):
                reg_doc.partner = persons[reg_meta.partner_name]
                reg_doc.save()

                #create a copy
                reg_doc.id = None
                reg_doc.person, reg_doc.partner = reg_doc.partner, reg_doc.person
                if reg_doc.dance_role:
                    reg_doc.dance_role = flip_role(reg_doc.dance_role)

                reg_doc.save(force_insert=True)
                registration_docs.append(reg_doc)

        price = sum([r.price for r in registration_docs])
        fee = price * 0.01
        status = payment_meta.status or SUCCESSFUL
        PaymentDocument(price=price, transaction_fee=fee, status=status,
                        event=new_event, paid_by=persons[payment_meta.name],
                        registrations=registration_docs).save(force_insert=True)

        event_meta.registration_docs.update({(reg.person.full_name, reg.product_key, reg.active): reg
                                             for reg in registration_docs})


class Flask(_Flask):
    testing = True
    secret_key = __name__

    def make_response(self, rv):
        if rv is None:
            rv = ''

        return super(Flask, self).make_response(rv)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_stripe():
    with mock.patch('salty_tickets.payments.stripe_session') as mock_stripe_session:
        mock_sp = Mock()
        mock_stripe_session.return_value.__enter__.return_value = mock_sp
        yield mock_sp


@pytest.fixture
def sample_stripe_card_error():
    return CardError('Sample card error', 'stripe_param', 123,
                     json_body={'error': 'Sample card error', 'message': 'Sample card error'})


@pytest.fixture
def sample_stripe_successful_charge():
    return {'id': 'ch_123', 'charge': 'CHARGE'}