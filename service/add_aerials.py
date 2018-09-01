from salty_tickets import sql_models, database
from salty_tickets.pricing_rules import create_partners_group

event = sql_models.Event.query.filter_by(id=1).one()
print(event.name)

order = sql_models.Order()
order.registration = sql_models.Registration(name='Chiara Liberti', email='cliberty@hotmail.it')
order.status = sql_models.ORDER_STATUS_PAID
database.db_session.add(order)
database.db_session.commit()

product = sql_models.Product.query.filter_by(name='Aerials Breakfast').one()
order_product = sql_models.OrderProduct(product, 0, {'dance_role':sql_models.DANCE_ROLE_FOLLOWER})
order_product.status = sql_models.ORDER_PRODUCT_STATUS_ACCEPTED
order_product.registrations.append(order.registration)

order_product_partner = sql_models.OrderProduct(product, 0, {'dance_role':sql_models.DANCE_ROLE_LEADER})
order_product_partner.status = sql_models.ORDER_PRODUCT_STATUS_ACCEPTED
registration_partner = sql_models.Registration(name='Roberto Bonato', email='cliberty@hotmail.it')
order_product_partner.registrations.append(registration_partner)

order.order_products.append(order_product)
order.order_products.append(order_product_partner)
database.db_session.commit()

create_partners_group(order_product, order_product_partner)