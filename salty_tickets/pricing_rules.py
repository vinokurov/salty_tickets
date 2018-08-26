from salty_tickets.database import db_session
from salty_tickets.emails import send_acceptance_from_waiting_list, send_acceptance_from_waiting_partner
from salty_tickets.sql_models import Event, Order, SignupGroup, SIGNUP_GROUP_PARTNERS, \
    Product, Registration, OrderProduct, ORDER_PRODUCT_STATUS_WAITING, \
    ORDER_STATUS_PAID, Payment, RegistrationGroup, SIGNUP_GROUP_FESTIVAL
from salty_tickets.mts_controllers import MtsSignupFormController
from salty_tickets.payments import stripe_amount, update_payment_total, transaction_fee
from salty_tickets.products import get_product_by_model, RegularPartnerWorkshop, CouplesOnlyWorkshop, \
    FestivalGroupDiscountProduct
from salty_tickets.tokens import order_product_deserialize, GroupToken


def get_order_for_event(event, form, registration=None, partner_registration=None):
    assert isinstance(event, Event)
    user_order = Order()

    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_form = form.get_product_by_key(product_model.product_key)
        if product.is_selected(product_form):
            order_product = product.get_order_product_model(product_model, product_form, form)
            if type(order_product) is list:
                order_product[0].registration = registration
                order_product[1].registration = partner_registration
                user_order.order_products.append(order_product[0])
                user_order.order_products.append(order_product[1])
            else:
                # registration_model = get_registration_from_form(form)
                order_product.registration = registration

                if product_form.needs_partner():
                    # partner_registration_model = get_partner_registration_from_form(form)
                    order_product.registration = partner_registration

                user_order.order_products.append(order_product)

    products_price = user_order.products_price
    user_order.transaction_fee = transaction_fee(products_price)
    user_order.total_price = user_order.products_price

    add_payment_to_user_order(user_order)

    return user_order


def add_payment_to_user_order(user_order):
    payment = Payment()

    for order_product in user_order.order_products:
        product = get_product_by_model(order_product.product)
        payment_item = product.get_payment_item(order_product)
        payment.payment_items.append(payment_item)

    update_payment_total(payment)
    payment.transaction_fee = transaction_fee(payment.amount)
    user_order.payments.append(payment)


def get_order_for_crowdfunding_event(event, form, registration=None, partner_registration=None):
    assert isinstance(event, Event)
    user_order = Order()

    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_form = form.get_product_by_key(product_model.product_key)
        price = product.get_total_price(product_model, product_form, form)
        if price > 0:
            # registration_model = get_registration_from_form(form)
            if hasattr(product_form, 'add'):
                print(product_form.add.object_data, type(product_form.add.object_data))
                print(product_form.add.object_data == None)
                if product_form.add.data not in ['0', 'None']:
                    for n in range(int(product_form.add.data)):
                        order_product = product.get_order_product_model(product_model, product_form, form)
                        order_product.registration = registration
                        user_order.order_products.append(order_product)
            else:
                order_product = product.get_order_product_model(product_model, product_form, form)
                order_product.registration = registration
                user_order.order_products.append(order_product)

    products_price = user_order.products_price
    user_order.transaction_fee = transaction_fee(products_price)
    user_order.total_price = user_order.products_price

    add_payment_to_user_order(user_order)

    return user_order


def get_total_raised(event):
    assert isinstance(event, Event)
    orders_query = event.orders.filter_by(status=ORDER_STATUS_PAID)
    total_stats = {
        'amount': sum([o.total_price for o in orders_query.all()]),
        'contributors': orders_query.count()
    }
    return total_stats


def get_stripe_properties(event, order, form):
    stripe_props = {}
    stripe_props['email'] = form.email.data
    stripe_props['amount'] = stripe_amount(order.payments[0])
    return stripe_props


def balance_event_waiting_lists(event_model):
    for product_model in event_model.products:
        product = get_product_by_model(product_model)
        if hasattr(product, 'balance_waiting_list'):
            results = product.balance_waiting_list(product_model)
            for order_product in results:
                send_acceptance_from_waiting_list(order_product)
            return results


def create_partners_group(order_product_1, order_product_2):
    group = SignupGroup(type=SIGNUP_GROUP_PARTNERS)
    group.event = order_product_1.order.event
    group.order_products.append(order_product_1)
    group.order_products.append(order_product_2)
    db_session.add(group)
    return group


def process_partner_registrations(user_order, form):
    for product_model in user_order.event.products:
        product = get_product_by_model(product_model)
        product_form = form.get_product_by_key(product_model.product_key)
        if isinstance(product, RegularPartnerWorkshop) and product_form.add.data:
            waiting_lists_couple = product.get_waiting_lists(product_model)[1]
            if product_form.partner_token.data:
                order_product = user_order.order_products.join(Product, aliased=True).filter_by(id=product_model.id).first()
                partner_order_product = order_product_deserialize(product_form.partner_token.data)
                group = create_partners_group(order_product, partner_order_product)
                db_session.add(group)
                if partner_order_product.status == ORDER_PRODUCT_STATUS_WAITING:
                    partner_role = partner_order_product.details_as_dict['dance_role']
                    if not waiting_lists_couple[partner_role]:
                        partner_order_product.accept()
                        send_acceptance_from_waiting_list(partner_order_product)
            elif product_form.add.data == 'couple':
                order_products = OrderProduct.query.filter_by(order_id=user_order.id). \
                    join(Product, aliased=True).filter_by(id=product_model.id).all()
                group = create_partners_group(order_products[0], order_products[1])
                db_session.add(group)
            db_session.commit()
        elif isinstance(product, CouplesOnlyWorkshop) and product_form.add.data:
            if product_form.partner_token.data:
                order_product = user_order.order_products.join(Product, aliased=True).filter_by(id=product_model.id).first()
                partner_order_product = order_product_deserialize(product_form.partner_token.data)
                group = create_partners_group(order_product, partner_order_product)
                db_session.add(group)

                partner_order_product.accept()
                send_acceptance_from_waiting_partner(partner_order_product)
            elif product_form.add.data == 'couple':
                order_products = OrderProduct.query.filter_by(order_id=user_order.id). \
                                    join(Product, aliased=True).filter_by(id=product_model.id).all()
                group = create_partners_group(order_products[0], order_products[1])
                db_session.add(group)
            db_session.commit()


def mts_get_order_for_event(event, form, registration=None, partner_registration=None):
    assert isinstance(event, Event)
    user_order = Order()

    free_classes_remaining = 0

    mts_form_controller = MtsSignupFormController(form)
    weekend_ticket_key = mts_form_controller.weekend_ticket_key
    if weekend_ticket_key:
        weekend_ticket_form = form.get_product_by_key(weekend_ticket_key)
        if mts_form_controller.full_pass_selected:
            free_classes_remaining = 3


    for product_model in event.products:
        product = get_product_by_model(product_model)
        product_form = form.get_product_by_key(product_model.product_key)
        if product.is_selected(product_form):
            order_product = product.get_order_product_model(product_model, product_form, form)
            if type(order_product) is list:

                if weekend_ticket_key:
                    product_keywords = product.keywords.split(',')
                    if weekend_ticket_form.includes and set(weekend_ticket_form.includes.split(',')).intersection(product_keywords):
                        order_product[0].price = 0
                        order_product[1].price = 0
                    elif isinstance(product, RegularPartnerWorkshop):
                        if free_classes_remaining:
                            order_product[0].price = 0
                            order_product[1].price = 0
                            free_classes_remaining -= 1
                        elif mts_form_controller.is_special_extra_block_price:
                            order_product[0].price = product.get_discount_price_by_key('extra_block')
                            order_product[1].price = product.get_discount_price_by_key('extra_block')

                order_product[0].registration = registration
                order_product[1].registration = partner_registration
                user_order.order_products.append(order_product[0])
                user_order.order_products.append(order_product[1])
            else:
                if weekend_ticket_key:
                    product_keywords = product.keywords.split(',')
                    if weekend_ticket_form.includes and set(weekend_ticket_form.includes.split(',')).intersection(product_keywords):
                        order_product.price = 0
                    elif isinstance(product, RegularPartnerWorkshop):
                        if free_classes_remaining:
                            order_product.price = 0
                            free_classes_remaining -= 1
                        elif mts_form_controller.is_special_extra_block_price:
                            order_product.price = product.get_discount_price_by_key('extra_block')

                # registration_model = get_registration_from_form(form)
                order_product.registration =registration

                if product_form.needs_partner():
                    # partner_registration_model = get_partner_registration_from_form(form)
                    order_product.registration = partner_registration

                user_order.order_products.append(order_product)

    products_price = user_order.products_price
    user_order.transaction_fee = transaction_fee(products_price)
    user_order.total_price = user_order.products_price

    add_payment_to_user_order(user_order)

    return user_order


def process_mts_group_registrations(user_order, form):
    group_discount_model = user_order.event.products.filter_by(type='FestivalGroupDiscountProduct').first()
    discount_product = get_product_by_model(group_discount_model)
    group_form = form.get_product_by_key(group_discount_model.product_key)
    if discount_product.is_selected(group_form) and \
            discount_product.get_total_price(group_discount_model, group_form, form):

        if group_form.group_participation.data == 'new':
            group = RegistrationGroup(
                name = group_form.group_name.data,
                location = group_form.location.data,
                description = group_form.group_description.data,
                event_id=user_order.event.id
            )
            db_session.add(group)
            db_session.commit()
        else:
            serialiser = GroupToken()
            group = serialiser.deserialize(group_form.group_token.data.strip())
        registrations = Registration.query.join(OrderProduct, aliased=False).filter_by(order_id=user_order.id).all()

        for reg in registrations:
            reg.registration_group = group

        db_session.commit()

