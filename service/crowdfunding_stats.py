from salty_tickets.sql_models import Event
from salty_tickets import products

for order in Event.query.filter_by(id=2).one().orders:
    print(order.registration.name, order.registration.email, order.registration.registered_datetime, order.status, order.total_price)
    for order_product in order.order_products:
        print('\t', order_product.product.name, order_product.price)
