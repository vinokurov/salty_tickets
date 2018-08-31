from salty_tickets.forms import get_primary_personal_info_from_form, get_partner_personal_info_from_form
from salty_tickets.models.order import Purchase, Order
from salty_tickets.pricers import ProductPricer


def register(event, form):
    personal_info = get_primary_personal_info_from_form(form)
    purchase_items = register_primary(event, form)
    partner_purchase_items = register_partner(event, form) or []
    purchase_items += partner_purchase_items

    purchase = Purchase(purchase_items)
    pricer = ProductPricer.from_event(event)
    pricer.price(purchase)

    order = Order(
        full_name=personal_info.full_name,
        email=personal_info.full_name,
        purchases=[purchase]
    )
    order.update_total_price()


def register_primary(event, form):
    personal_info = get_primary_personal_info_from_form(form)
    purchase_items = []
    for product_key, product in event.products.items():
        product_form_data = form.get_product_by_key(product_key)
        if product.is_added(product_form_data):
            purchase_items.append(product.get_purchase_item(product_form_data, personal_info))
    return purchase_items


def register_partner(event, form):
    personal_info = get_partner_personal_info_from_form(form)
    if personal_info:
        purchase_items = []
        for product_key, product in event.products.items():
            product_form_data = form.get_product_by_key(product_key)
            if product.is_added(product_form_data):
                purchase_items.append(product.get_partner_purchase_item(product_form_data, personal_info))
        return purchase_items or None


def registration_payment_success(event, registration, payment_details):
    pass


def registration_payment_failed(event, registration, payment_details):
    pass
