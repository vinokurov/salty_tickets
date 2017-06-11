import datetime

import pytest
from salty_tickets.forms import create_event_form, SignupForm, FormWithProducts
from salty_tickets.products import CouplesOnlyWorkshop
from salty_tickets.models import Product, Event
from wtforms import Form


def test_CouplesOnlyWorkshop_get_discount_price():
    product = CouplesOnlyWorkshop(
        name='Aerials Workshop - Morning',
        info='Sunday morning aerials workshop with Pol & Sara.',
        max_available=10,
        price=50,
        discount_prices='{"aerials_full_day": 40}'
    )

    form = product.get_form()

    form.add.data = False
    assert product.get_discount_price_by_key('aerials_full_day') == 40


def test_CouplesOnlyWorkshop_get_total_price():
    event = Event(
        name='Salty Recipes with Pol & Sara',
        start_date=datetime.datetime(2017, 7, 29),
        event_type='dance'
    )

    product1 = CouplesOnlyWorkshop(
        name='Aerials Workshop - Morning',
        info='Sunday morning aerials workshop with Pol & Sara.',
        max_available=10,
        price=50,
        discount_prices='{"aerials_full_day": 40}'
    )
    product2 = CouplesOnlyWorkshop(
        name='Aerials Workshop - Afternoon',
        info='Sunday morning aerials workshop with Pol & Sara.',
        max_available=10,
        price=45,
        discount_prices='{"aerials_full_day": 30}'
    )

    event.products.append(product1.model)
    event.products.append(product2.model)

    product1_key = product1.model.product_key
    product1_form = product1.get_form()

    product2_key = product2.model.product_key
    product2_form = product2.get_form()

    class EventForm(Form, FormWithProducts):
        product_keys = [product1_key, product2_key]

    setattr(EventForm, product1_key, product1_form)
    setattr(EventForm, product2_key, product2_form)

    order_form = EventForm()

    order_form.get_product_by_key(product1_key).add.data = False
    order_form.get_product_by_key(product2_key).add.data = False
    assert product1.get_total_price(product1_form, order_form) == 0

    order_form.get_product_by_key(product1_key).add.data = True
    order_form.get_product_by_key(product2_key).add.data = False
    assert product1._get_discount_keys() == ['aerials_full_day']
    assert product1._get_applicable_discount_keys(product1_form, order_form) == []
    assert product1.get_total_price(product1_form, order_form) == 50

    order_form.get_product_by_key(product1_key).add.data = True
    order_form.get_product_by_key(product2_key).add.data = True
    assert product1._get_discount_keys() == ['aerials_full_day']
    assert product1._get_applicable_discount_keys(product1_form, order_form) == ['aerials_full_day']
    assert product1.get_total_price(product1_form, order_form) == 40
    assert product2.get_total_price(product2_form, order_form) == 30

