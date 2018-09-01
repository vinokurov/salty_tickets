from salty_tickets.database import db_session
from salty_tickets.sql_models import Registration, Order, OrderProduct, Event, Product, CrowdfundingRegistrationProperties

event = Event.query.filter_by(event_key='simona_de_leo_s_crowdfunding_campaign').one()

donate_product = Product.query.filter_by(id=1).one()
patrick_private = Product.query.filter_by(id=5).one()

registration1 = Registration(
    name='Aleksandr Vinokurov',
    email='alexander.a.vinokurov@gmail.com',
    comment='Good luck with getting the MA! All the best!',
    registered_datetime='2017-05-28 18:18:57'
)
registration1.crowdfunding_registration_properties = \
                CrowdfundingRegistrationProperties(anonymous=1)
order1 = Order(
    total_price=20,
    transaction_fee=0.5,
    status='paid',
    order_datetime='2017-05-28 18:18:57',
    stripe_charge_id='ch_1AOVyfHQoe2Uj5fJugrd2ZhT'
)
order1.registration = registration1
order1_product = OrderProduct(
    price=order1.total_price,
    product=donate_product
)
order1.order_products.append(order1_product)
event.orders.append(order1)

registration2 = Registration(
    name='Noelle',
    email='noellendb@yahoo.co.uk',
    comment='Happy Birthday gorgeous and enjoy your MA!! ',
    registered_datetime='2017-05-29 13:41:31'
)
registration2.crowdfunding_registration_properties = \
                CrowdfundingRegistrationProperties(anonymous=0)
order2 = Order(
    total_price=25,
    transaction_fee=0.575,
    status='paid',
    order_datetime='2017-05-29 13:41:31',
    stripe_charge_id='ch_1AOo7iHQoe2Uj5fJ78wy9Z3p'
)
order2.registration = registration2
order2_product = OrderProduct(
    price=order2.total_price,
    product=donate_product
)
order2.order_products.append(order2_product)
event.orders.append(order2)

registration3 = Registration(
    name='Chott Andersen',
    email='chottmcanders@gmail.com',
    comment='',
    registered_datetime='2017-05-30 11:54:43'
)
registration3.crowdfunding_registration_properties = \
                CrowdfundingRegistrationProperties(anonymous=1)
order3 = Order(
    total_price=35,
    transaction_fee=0.725,
    status='paid',
    order_datetime='2017-05-30 11:54:43',
    stripe_charge_id='ch_1AP8vuHQoe2Uj5fJqsHAUKvo'
)
order3.registration = registration3
order3_product = OrderProduct(
    price=order3.total_price,
    product=patrick_private
)
order3.order_products.append(order3_product)
event.orders.append(order3)


db_session.commit()

