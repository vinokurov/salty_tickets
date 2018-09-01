from datetime import datetime

import pytest
from mock import MagicMock
from salty_tickets.forms import create_event_form, DanceSignupForm, get_primary_personal_info_from_form
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct
from flask import Flask as _Flask


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
    return app

@pytest.fixture
def client(app):
    return app.test_client()


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
    form = MagicMock()
    form.name.data = 'My Name'
    form.email.data = 'email@email.com'
    form.comment.data = 'My comment'

    info = get_primary_personal_info_from_form(form)
    assert info.full_name == 'My Name'
    assert info.email == 'email@email.com'
    assert info.comment == 'My comment'


def test_event_form_validation(app, client):
    post_data = {'name': 'test'}

    @app.route('/', methods=['POST'])
    def index():
        event = Event(name='Salty Recipes', key='salty_recipes',
                      start_date=datetime(2018, 10, 11, 10, 0), end_date=datetime(2018, 10, 11, 16, 0))
        form = create_event_form(event)()
        assert form.name.data == post_data['name']
        info = get_primary_personal_info_from_form(form)
        assert info.full_name == post_data['name']

    client.post('/', data=post_data)
