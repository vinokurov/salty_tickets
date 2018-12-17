from salty_tickets.constants import SUCCESSFUL
from salty_tickets.dao import TicketsDAO, PaymentDocument, id_filter, TransactionDocument
from salty_tickets.config import MONGO

dao = TicketsDAO(MONGO)
event = dao.get_event_by_key('mind_the_shag_2019')
payments = dao.get_payments_by_event(event)

for payment in payments:
    if payment.status == SUCCESSFUL:
        print(payment.id, payment.date, payment.paid_by.full_name)
        payment_doc = PaymentDocument.objects(**id_filter(payment.id)).first()
        transaction = TransactionDocument(
            price=payment.price,
            transaction_fee=payment.transaction_fee,
            description='Card payment',
            success=True
        )
        if payment.stripe.charges:
            transaction.stripe_charge_id = payment.stripe.charges[0]
        payment_doc.transactions = [transaction]
        payment_doc.save()
