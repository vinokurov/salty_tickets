from collections import namedtuple

from salty_tickets.forms import get_registration_from_form, get_partner_registration_from_form
from salty_tickets.products import get_product_by_model
from salty_tickets.models import Event, ProductParameter, Order, OrderProduct, Product, ORDER_PRODUCT_STATUS_WAITING

__author__ = 'vnkrv'


def get_salty_recipes_price(form):
    price_aerieals_one_day = 50
    price_aerials_both_days = 90
    price_shag_one_day = 35
    price_shag_both_days = 50

    total = 0
    if form.saturday_aerials.going.data and form.sunday_aerials.going.data:
        total += price_aerials_both_days
    elif form.saturday_aerials.going.data or form.sunday_aerials.going.data:
        total += price_aerieals_one_day

    if form.saturday_shag.going.data and form.sunday_shag.going.data:
        total += price_shag_both_days
    elif form.saturday_shag.going.data or form.sunday_shag.going.data:
        total += price_shag_one_day

    return total


def get_order_for_event(event, form, registration=None, partner_registration=None):
    assert isinstance(event, Event)
    user_order = Order()

    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_form = form.get_product_by_key(product_model.product_key)
        price = product.get_total_price(product_form, form)
        if price > 0:
            order_product = product.get_order_product_model(product_model, product_form, form)
            if type(order_product) is list:
                order_product[0].registrations.append(registration)
                order_product[1].registrations.append(partner_registration)
                user_order.order_products.append(order_product[0])
                user_order.order_products.append(order_product[1])
            else:
                # registration_model = get_registration_from_form(form)
                order_product.registrations.append(registration)

                if product_form.needs_partner():
                    # partner_registration_model = get_partner_registration_from_form(form)
                    order_product.registrations.append(partner_registration)

                user_order.order_products.append(order_product)

    products_price = user_order.products_price
    user_order.transaction_fee = transaction_fee(products_price)
    user_order.total_price = user_order.products_price


    return user_order


def get_order_for_crowdfunding_event(event, form):
    assert isinstance(event, Event)
    user_order = Order()

    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_form = form.get_product_by_key(product_model.product_key)
        price = product.get_total_price(product_form)
        if price > 0:
            registration_model = get_registration_from_form(form)
            if hasattr(product_form, 'add'):
                for n in range(int(product_form.add.data)):
                    user_order.order_products.append(
                        OrderProduct(product_model, price, registration=registration_model))
            else:
                user_order.order_products.append(
                    OrderProduct(product_model, price, registration=registration_model))

    products_price = user_order.products_price
    user_order.transaction_fee = transaction_fee(products_price)
    user_order.total_price = user_order.products_price

    return user_order


def transaction_fee(price):
    return price * 0.015 + 0.2


def get_total_raised(event):
    assert isinstance(event, Event)
    total_stats = {
        'amount': sum([sum([o.total_price for o in r.orders]) for r in event.registrations.join(Order).all()]),
        'contributors': len(event.registrations.join(Order).all())
    }
    return total_stats


def get_stripe_properties(event, order, form):
    stripe_props = {}
    stripe_props['email'] = form.email.data
    stripe_props['amount'] = order.stripe_amount
    return stripe_props


OrderProductTuple = namedtuple('OrderProductTuple', ['name', 'price', 'wait_list'])


class OrderSummaryController:
    products = []
    transaction_fee = ''
    total_price = ''
    show_order_summary = False

    def __init__(self, order):
        assert isinstance(order, Order)
        self.transaction_fee = '{:.2f}'.format(order.transaction_fee)
        total_price = order.total_price + order.transaction_fee
        self.total_price = '{:.2f}'.format(total_price)

        products = []
        for order_product in order.order_products.all():
            price = '{:.2f}'.format(order_product.price)
            product = get_product_by_model(order_product.product)
            if hasattr(product, 'get_name'):
                name = product.get_name(order_product)
            else:
                name = order_product.product.name
            wait_list = order_product.details_as_dict['status'] == ORDER_PRODUCT_STATUS_WAITING
            products.append(OrderProductTuple(name=name, price=price, wait_list=wait_list))
        self.products = products
        self.show_order_summary = len(self.products) > 0

