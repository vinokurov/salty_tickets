from salty_tickets import sql_models
from salty_tickets import database
from salty_tickets.sql_models import Order, Payment, PaymentItem, PAYMENT_STATUS_PAID

sql_models.Base.metadata.create_all(bind=database.engine)
database.db_session.commit()

sql = "ALTER TABLE orders ADD payment_due FLOAT NOT NULL DEFAULT 0;"
database.db_session.execute(sql)
database.db_session.commit()

for order in Order.query.all():
    payment = Payment(
        payment_datetime=order.order_datetime,
        amount=order.total_price,
        transaction_fee=order.transaction_fee,
        stripe_charge_id=order.stripe_charge_id,
        status=PAYMENT_STATUS_PAID,
    )
    order.payments.append(payment)
    for op in order.order_products:
        item = PaymentItem(
            order_product_id=op.id,
            amount=op.price_all
        )
        payment.payment_items.append(item)
database.db_session.commit()
