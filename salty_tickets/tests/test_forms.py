from datetime import datetime

import pytest
from mock import MagicMock, Mock
from pytest import raises
from salty_tickets.constants import COUPLE, LEADER, FOLLOWER
from salty_tickets.forms import create_event_form, DanceSignupForm, get_primary_personal_info_from_form, \
    need_partner_check
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct, RegistrationProduct, PartnerProductForm, PartyProduct
from wtforms import ValidationError


@pytest.fixture
def sample_event():
    """Sample event with 2 workshops and 1 party"""
    event = Event(name='Sample Event')
    event.append_products([
        WorkshopProduct(name='WS 1', base_price=15.0, max_available=10, ratio=1.5),
        WorkshopProduct(name='WS 2', base_price=15.0, max_available=10, ratio=1.5),
        PartyProduct(name='Main Party', base_price=5.0, max_available=20)
    ])
    return event


def test_create_event_form(app):
    event = Event(name='Salty Recipes', key='salty_recipes',
                  start_date=datetime(2018, 10, 11, 10, 0), end_date=datetime(2018, 10, 11, 16, 0))

    products = [
        WorkshopProduct(name='Morning WS', base_price=15.0, max_available=10, ratio=1.5, start_datetime=datetime(2018, 10, 11, 10, 0), end_datetime=datetime(2018, 10, 11, 12, 0)),
        WorkshopProduct(name='Evening WS', base_price=15.0, max_available=10, ratio=1.5, start_datetime=datetime(2018, 10, 11, 15, 0), end_datetime=datetime(2018, 10, 11, 16, 0)),
    ]
    event.append_products(products)

    form_class = create_event_form(event)
    assert issubclass(form_class, DanceSignupForm)

    form = form_class()
    assert form.get_product_by_key(products[0].key).form_class == products[0].get_form_class()


def test_get_primary_personal_info_from_form():
    form = MagicMock(spec=DanceSignupForm)
    form.name.data = 'My Name'
    form.email.data = 'email@email.com'
    form.comment.data = 'My comment'

    person = get_primary_personal_info_from_form(form)
    assert person.full_name == 'My Name'
    assert person.email == 'email@email.com'
    assert person.comment == 'My comment'

    person1 = get_primary_personal_info_from_form(form)
    assert person is person1


def test_need_partner_check():
    product_1 = Mock()
    product_2 = Mock()

    event = Event(name='Salty Recipes', products={'p1': product_1, 'p2': product_2})
    event_form = Mock()
    form_field = Mock()

    # field is empty and products require partner info
    form_field.data = None
    product_1.needs_partner.return_value = True
    product_2.needs_partner.return_value = False
    with raises(ValidationError):
        need_partner_check(event, event_form, form_field)

    # field is empty but products don't require partner info
    form_field.data = None
    product_1.needs_partner.return_value = False
    product_2.needs_partner.return_value = False
    assert not need_partner_check(event, event_form, form_field)

    # field is not empty
    form_field.data = 'Some text'
    product_1.needs_partner.return_value = True
    product_2.needs_partner.return_value = False
    assert not need_partner_check(event, event_form, form_field)


@pytest.mark.parametrize('post_data', [
    {'name': 'Mr One', 'email': 'aa@bb.cc'},
    {'name': 'Mr One', 'email': 'aa@bb.cc', 'ws_1-add': LEADER},
    {'name': 'Mr One', 'email': 'aa@bb.cc', 'ws_1-add': FOLLOWER},
    {'name': 'Mr One', 'email': 'aa@bb.cc', 'ws_1-add': FOLLOWER, 'ws_2-add': FOLLOWER},
    {'name': 'Mr One', 'email': 'aa@bb.cc', 'dance_role': LEADER, 'partner_name': 'Ms One', 'partner_email': 'bb@cc.dd', 'ws_1-add': 'couple'},
    {'name': 'Mr One', 'email': 'aa@bb.cc', 'dance_role': LEADER, 'partner_name': 'Ms One', 'partner_email': 'bb@cc.dd', 'ws_1-add': 'couple', 'ws_2-add': 'couple'},
])
def test_event_form_validation_success(app, client, sample_event, post_data):
    @app.route('/', methods=['POST'])
    def index():
        form = create_event_form(sample_event)()
        valid = form.validate_on_submit()
        assert form.errors == {}
        assert valid

    client.post('/', data=post_data)


@pytest.mark.parametrize('post_data,invalid_fields', [
    ({'name': 'Mr One'}, ['email']),
    ({'name': 'Mr One', 'email': 'aa@bb.cc', 'ws_1-add': COUPLE}, ['partner_name', 'partner_email', 'dance_role']),
    ({'name': 'Mr One', 'email': 'aa@bb.cc', 'partner_name': 'Ms One', 'partner_email': 'bb@cc.dd', 'ws_1-add': COUPLE}, ['dance_role']),
    ({'name': 'Mr One', 'email': 'aa@bb.cc', 'ws_1-add': LEADER, 'ws_2-add': COUPLE}, ['partner_name', 'partner_email', 'dance_role']),
    ({'name': 'Mr One', 'email': 'aa@bb.cc', 'ws_1-add': 'WRONG'}, ['ws_1']),
])
def test_event_form_validation_fail(app, client, sample_event, post_data, invalid_fields):
    @app.route('/', methods=['POST'])
    def index():
        form = create_event_form(sample_event)()
        assert not form.validate_on_submit()
        for f in invalid_fields:
            assert f in form.errors

    client.post('/', data=post_data)
