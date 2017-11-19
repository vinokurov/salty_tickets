from salty_tickets import models, database

event = models.Event.query.filter_by(id=1).one()
print(event.name)

order = models.Order()
order.registration = models.Registration(name='Neal Jackson', email='nealjc@aol.com')
order.status = models.ORDER_STATUS_PAID
database.db_session.add(order)
database.db_session.commit()

product = models.Product.query.filter_by(name='Collegiate Shag').one()
order_product = models.OrderProduct(product, 0, {'dance_role':models.DANCE_ROLE_LEADER})
order_product.status = models.ORDER_PRODUCT_STATUS_ACCEPTED
order_product.registrations.append(order.registration)

order.order_products.append(order_product)
database.db_session.commit()