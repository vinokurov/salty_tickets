from salty_tickets.database import db_session
from salty_tickets.models import Event, Registration, Order, Product, OrderProduct, Payment, OrderProductDetail
from salty_tickets.tokens import order_serialize

event = Event.query.filter_by(id=6).one()
registration = Registration(
    name='Freeman Bacon',
    email='dance@freemanbacon.com',
    comment='manually added',
    country='UK',
    city='London',
    event_id = event.id
)

def get_order_product(product_name, price):
    order_product = OrderProduct(
        Product.query.filter_by(event_id=6,name=product_name).one(),
        price=price,
        status='accepted'
    )
    order_product.registration = registration
    return order_product


def get_station_order_product(product_name, price, dance_role):
    order_product = get_order_product(product_name, price)
    order_product.details.append(OrderProductDetail(field_name='dance_role', field_value=dance_role))
    return order_product

user_order = Order()

# user_order.order_products.append(get_station_order_product('Rhythm Shag', 0, 'follower'))
# user_order.order_products.append(get_station_order_product('Swing Out Like You\'re From St. Louis', 0, 'follower'))
# user_order.order_products.append(get_station_order_product('Rockabilly Bopper Shag', 0, 'follower'))
user_order.order_products.append(get_order_product('Friday Party', 0))
user_order.order_products.append(get_order_product('Saturday Party', 0))
user_order.order_products.append(get_order_product('Sunday Party', 0))
# user_order.order_products.append(get_order_product('Full Weekend Ticket', 135))

# enable for free registrations:
# user_order.payments[0].amount = 0

# user_order.total_price = sum([op.price for op in user_order.order_products])
user_order.total_price = user_order.products_price
user_order.payment_due = user_order.total_price

user_order.payments.append(Payment(amount=0))

user_order.registration = registration
event.orders.append(user_order)
db_session.commit()

token = order_serialize(user_order)
print(token)

