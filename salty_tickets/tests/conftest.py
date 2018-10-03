import pymongo
import typing
from unittest import mock
from unittest.mock import Mock

from datetime import datetime

import pytest
from dataclasses import dataclass
from flask import Flask as _Flask
from flask.testing import FlaskClient
from flask_session import Session
from mongoengine import connect
from salty_tickets.constants import LEADER, FOLLOWER, SUCCESSFUL, FAILED
from salty_tickets.dao import EventDocument, RegistrationDocument, ProductRegistrationDocument, \
    PaymentDocument, TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct, PartyProduct, BaseProduct
from salty_tickets.models.registrations import PersonInfo
from salty_tickets.api.registration_process import do_check_partner_token, do_get_payment_status, do_pay, do_checkout, \
    do_price
from salty_tickets.utils.utils import jsonify_dataclass
from salty_tickets.waiting_lists import flip_role
from stripe import Charge, Customer
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
            WorkshopProduct(name='Saturday', base_price=25.0, max_available=15, ratio=1.3, allow_first=2, tags={'full'}),
            WorkshopProduct(name='Sunday', base_price=25.0, max_available=15, ratio=1.3, allow_first=2, tags={'full'}),
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
                reg_doc = ProductRegistrationDocument(**kwargs)
                reg_doc.partner = persons[reg_meta.partner_name]
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
    app.config['SESSION_TYPE'] = 'mongodb'
    app.config['SESSION_MONGODB'] = pymongo.MongoClient()
    Session(app)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_routes(app, test_dao):
    @app.route('/price', methods=['POST'])
    def _price():
        return jsonify_dataclass(do_price(test_dao, 'salty_recipes'))

    @app.route('/checkout', methods=['POST'])
    def _checkout():
        return jsonify_dataclass(do_checkout(test_dao, 'salty_recipes'))

    @app.route('/pay', methods=['POST'])
    def _pay():
        return jsonify_dataclass(do_pay(test_dao))

    @app.route('/payment_status', methods=['POST'])
    def _payment_status():
        return jsonify_dataclass(do_get_payment_status(test_dao))

    @app.route('/check_partner_token', methods=['POST'])
    def _check_partner_token():
        return jsonify_dataclass(do_check_partner_token(test_dao))

    @app.route('/user_order', methods=['GET'])
    def user_order_index():
        pass


@pytest.fixture
def mock_send_email():
    with mock.patch('salty_tickets.emails.send_email') as mock_1,\
         mock.patch('salty_tickets.api.registration_process.send_registration_confirmation') as mock_2,\
         mock.patch('salty_tickets.api.registration_process.send_waiting_list_accept_email') as mock_3:
        mock_1.return_value = True
        mock_2.return_value = True
        mock_3.return_value = True
        yield


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
    charge = Charge(id='ch_123')
    # return {'id': 'ch_123', 'charge': 'CHARGE'}
    return charge


@pytest.fixture
def sample_stripe_customer():
    charge = Customer(id='cus_123')
    # return {'id': 'ch_123', 'charge': 'CHARGE'}
    return charge


NAMES = [
    'Simonne Smithson',
    'Gregg Defoor',
    'Darrel Harting',
    'Guy Newquist',
    'Jimmy Beesley',
    'Hal Nogueira',
    'Shaunta Kaul',
    'Gaylene Guillaume',
    'Hobert Weatherholtz',
    'Sari Sasson',
    'Terrell Moorehead',
    'Jina Knarr',
    'Brain Marse',
    'Sammie Le',
    'Tamera Clymer',
    'Granville Bien',
    'Lakesha Carreno',
    'Kittie Pal',
    'Sung Edgell',
    'Frederic Mcgehee',
    'Sharie Sack',
    'Kacie Sheley',
    'Marketta Gehl',
    'Tamie Mcpeak',
    'Reita Ealy',
    'Annamaria Yamada',
    'Andres Bastarache',
    'Anisha Balzer',
    'Camellia Barren',
    'Elizabet Madera',
    'Stephen Bosse',
    'Mason Shofner',
    'Dudley Blake',
    'Garland Grosso',
    'Richie Germano',
    'Al Mckoy',
    'Elida Leary',
    'Trish Scipio',
    'Gema Lang',
    'Carlo Gaddis',
    'Joleen Batey',
    'Heike Onorato',
    'Elroy Durrant',
    'Tabetha Manus',
    'Jani Attaway',
    'Windy Holle',
    'Janise Desilva',
    'Keli Wiley',
    'Princess Sande',
    'Tammi Speier',
]


class PersonFactory:
    _names: typing.List[str]

    def __init__(self):
        self._names = NAMES.copy()

    def pop(self, location=None):
        name = self._names.pop()
        email = name.replace(' ', '.') + '@mail.com'
        return PersonInfo(full_name=name, email=email)


@pytest.fixture
def person_factory():
    return PersonFactory()


@dataclass
class AllVars:
    dao: TicketsDAO
    app: Flask
    client: FlaskClient
    person_factory: PersonFactory
    mock_send_email: Mock
    mock_stripe: Mock
    sample_stripe_card_error: CardError
    sample_stripe_successful_charge: typing.Dict
    sample_stripe_customer: typing.Dict


@pytest.fixture
def e2e_vars(test_dao, salty_recipes, app, app_routes, client, person_factory,
             mock_stripe, sample_stripe_card_error, sample_stripe_successful_charge,
             sample_stripe_customer, mock_send_email):

    return AllVars(test_dao, app, client, person_factory, mock_send_email,
                   mock_stripe, sample_stripe_card_error, sample_stripe_successful_charge,
                   sample_stripe_customer)
