from .forms import get_registration_from_form
from .products import get_product_by_model
from .models import Event, ProductParameter, Order, OrderProduct, Product

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


def get_order_for_event(event, form):
    assert isinstance(event, Event)
    user_order = Order()

    for product in event.products:
        product_form = form.get_product_by_key(product.product_key)
        if product_form.going.data:
            weekend_key = product.parameters.filter(ProductParameter.parameter_name == "weekend_key").first().parameter_value

            # check if we can apply weekend discount
            discount_related_products = event.products.join(ProductParameter).filter(
                                        ProductParameter.parameter_name == "weekend_key",
                                        ProductParameter.parameter_value == weekend_key
            ).all()

            # TODO: should also include previously ordered and paid products
            discount_applies = [form.get_product_by_key(p.product_key).going.data
                                for p in discount_related_products].count(False) == 0
            print(weekend_key)
            print(discount_related_products)
            print([form.get_product_by_key(p.product_key).going.data for p in discount_related_products])
            if discount_applies:
                price_str = product.parameters.filter(ProductParameter.parameter_name == "price_weekend").first().parameter_value
            else:
                price_str = product.parameters.filter(ProductParameter.parameter_name == "base_price").first().parameter_value

            price = float(price_str)
            user_order.order_products.append(OrderProduct(product, price))
            print(product.name, price, discount_applies)

    products_price = user_order.products_price
    print(products_price)
    user_order.transaction_fee = transaction_fee(products_price)
    total_price = products_price + float(user_order.transaction_fee)
    user_order.total_price = "%.2f" % total_price

    return user_order


def get_order_for_crowdfunding_event(event, form):
    assert isinstance(event, Event)
    user_order = Order()

    for product_model in event.products:
        print(product_model)
        product = get_product_by_model(product_model)
        product_form = form.get_product_by_key(product_model.product_key)
        price = product.get_total_price(product_form)
        if price > 0:
            registration_model = get_registration_from_form(form)
            user_order.order_products.append(OrderProduct(product_model, price, registration=registration_model))

    products_price = user_order.products_price
    print(products_price)
    user_order.transaction_fee = transaction_fee(products_price)
    total_price = products_price + float(user_order.transaction_fee)
    user_order.total_price = "%.2f" % total_price

    return user_order


def transaction_fee(price):
    return "%.2f" % (price*0.015 + 0.2)


def get_total_raised(event):
    assert isinstance(event, Event)
    total_stats = {
        'amount': sum([sum([o.total_price - o.transaction_fee for o in r.orders]) for r in event.registrations.join(Order).all()]),
        'contributors': len(event.registrations.join(Order).all())
    }
    return total_stats


def get_stripe_properties(event, order, form):
    stripe_props = {}
    stripe_props['email'] = form.email.data
    stripe_props['amount'] = int(float(order.total_price)*100)
    return stripe_props

