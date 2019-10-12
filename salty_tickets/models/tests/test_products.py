from flask import Flask as _Flask
import pytest
from salty_tickets.forms import create_event_form
from salty_tickets.models.event import Event
from salty_tickets.models.products import Product
from salty_tickets.models.registrations import Purchase, Person


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


def test_product(app):
    product = Product(
        name='Tote Bag',
        key='bag',
        base_price=25.0,
        options={'red': 'Burgundy Red', 'blue': 'Navy Blue'}
    )
    event = Event(name='Test', products={'bag': product})
    with app.app_context():
        form = create_event_form(event)()

    form.get_item_by_key('bag').add.data = {'red': 1}
    expected_purchases = [Purchase(person=Person('You', ''),
                                   product_key='bag',
                                   product_option_key='red',
                                   amount=1,
                                   description='Tote Bag / Burgundy Red',
                                   price=25.0,
                                   price_each=25.0)]
    assert expected_purchases == product.parse_form(form)

    form.get_item_by_key('bag').add.data = {'blue': 2}
    expected_purchases = [Purchase(person=Person('You', ''),
                                   product_key='bag',
                                   product_option_key='blue',
                                   amount=2,
                                   description='Tote Bag / Navy Blue',
                                   price=50.0,
                                   price_each=25.0)]
    assert expected_purchases == product.parse_form(form)

    with app.app_context():
        form = create_event_form(event)()
    form.get_item_by_key('bag').add.data = {'blue': 2}
    form.name.data = 'Mr.X'
    form.email.data = 'mr.x@gmail.com'
    expected_purchases[0].person = Person('Mr.X', 'mr.x@gmail.com')
    assert expected_purchases == product.parse_form(form)

    form.get_item_by_key('bag').add.data = {'blue': 2, 'red': 1}
    expected_purchases = [Purchase(person=Person('Mr.X', 'mr.x@gmail.com'),
                                   product_key='bag',
                                   product_option_key='blue',
                                   amount=2,
                                   description='Tote Bag / Navy Blue',
                                   price=50.0,
                                   price_each=25.0),
                          Purchase(person=Person('Mr.X', 'mr.x@gmail.com'),
                                   product_key='bag',
                                   product_option_key='red',
                                   amount=1,
                                   description='Tote Bag / Burgundy Red',
                                   price=25.0,
                                   price_each=25.0)
                          ]
    assert expected_purchases == product.parse_form(form)
