from salty_tickets.sql_models import Event
from salty_tickets import products

for product_model in Event.query.filter_by(id=5).one().products:
    print(product_model.name)
    product = products.get_product_by_model(product_model)
    print('\t',product.get_registration_stats(product_model))
    for order_product in product_model.product_orders:
        if order_product.order.status == 'paid':
            print('\t', order_product.registrations[0].name, order_product.registrations[0].email, order_product.details_as_dict['dance_role'], order_product.status)
