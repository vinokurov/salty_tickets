from salty_tickets import sql_models
from salty_tickets.controllers import OrderSummaryController
from salty_tickets.database import db_session
from salty_tickets.sql_models import Registration, Order, ORDER_PRODUCT_STATUS_ACCEPTED, OrderProduct, DANCE_ROLE_LEADER, DANCE_ROLE_FOLLOWER, \
    ORDER_STATUS_PAID, PAYMENT_STATUS_PAID
from salty_tickets.pricing_rules import add_payment_to_user_order, balance_event_waiting_lists

event = sql_models.Event.query.filter_by(event_key='salty_recipes_with_simona_rokas').one()
print(event.name)

NAME = 'Louis Carruthers'
EMAIL = 'Louis93@live.co.uk'
PRICE = 0
ROLE = DANCE_ROLE_LEADER
#ROLE = DANCE_ROLE_FOLLOWER

registration = Registration(
        name=NAME,
        email=EMAIL,
        comment='Manually added'
)

user_order = Order()
for product_model in event.products:
    order_product = OrderProduct(
        product_model,
        PRICE,
        dict(dance_role=ROLE),
        status=ORDER_PRODUCT_STATUS_ACCEPTED
    )
    order_product.registrations.append(registration)
    user_order.order_products.append(order_product)

user_order.transaction_fee = 0
user_order.total_price = user_order.products_price

user_order.registration = registration
add_payment_to_user_order(user_order)

total_paid = sum([p.amount for p in user_order.payments]) or 0
user_order.payment_due = user_order.total_price - total_paid

# has_paid = any([p.status == PAYMENT_STATUS_PAID for p in user_order.payments])
user_order.status = ORDER_STATUS_PAID

event.orders.append(user_order)

db_session.commit()

balance_results = balance_event_waiting_lists(event)

order_summary_controller = OrderSummaryController(user_order)
print(order_summary_controller.token)

