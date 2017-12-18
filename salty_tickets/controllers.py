from datetime import datetime, timedelta

from flask import url_for
from salty_tickets.models import Event, OrderProduct, Order, Registration, ORDER_PRODUCT_STATUS_WAITING, SignupGroup, \
    SIGNUP_GROUP_TYPE_PARTNERS, group_order_product_mapping
from salty_tickets.products import get_product_by_model
from salty_tickets.tokens import email_deserialize, order_product_serialize, order_product_deserialize, order_serialize, \
    GroupToken


def price_format(func):
    def func_wrap(self):
        return '£{:.2f}'.format(func(self))
    return func_wrap


def timestamp_format(func):
    def func_wrap(self):
        return '{:%d-%b-%Y %H:%M}'.format(func(self))
    return func_wrap


class PaymentController:
    def __init__(self, payment):
        self._payment = payment




class OrderProductController:
    def __init__(self, order_product):
        self._order_product = order_product

    @classmethod
    def from_token(cls, order_product_token):
        order_product = order_product_deserialize(order_product_token)
        if order_product:
            return cls(order_product)

    @property
    def name(self):
        product = get_product_by_model(self._order_product.product)
        if hasattr(product, 'get_name'):
            return product.get_name(self._order_product)
        else:
            return self._order_product.product.name

    @property
    def price(self):
        return self._order_product.price

    @property
    def total_paid(self):
        return sum([item.amount for item in self._order_product.payment_items])

    @property
    def total_remaining(self):
        return self._order_product.price - sum([item.amount for item in self._order_product.payment_items])

    @property
    def status(self):
        return self._order_product.status.title()

    @property
    def is_waiting(self):
        return self._order_product.status == ORDER_PRODUCT_STATUS_WAITING

    @property
    def product_type(self):
        return self._order_product.product.type

    @property
    def token(self):
        return order_product_serialize(self._order_product)

    @property
    def _token_expiry(self):
        if self.product_type == 'RegularPartnerWorkshop' and not self.is_waiting:
            return self._order_product.order.order_datetime + timedelta(days=1)
        else:
            return None

    @property
    @timestamp_format
    def token_expiry(self):
        return self.token_expiry

    @property
    def cancel_url(self):
        return url_for('event_order_product_cancel',
                       event_key=self._order_product.order.event.event_key,
                       order_product_token=self.token,
                       _external=True)

    @property
    def can_add_partner(self):
        if self.product_type not in ('CouplesOnlyWorkshop', 'RegularPartnerWorkshop'):
            return False
        elif self.partner_order_product:
            return False
        elif self._token_expiry and datetime.now() > self._token_expiry:
            return False
        else:
            return True

    @property
    def partner_order_product(self):
        if self.product_type in ('CouplesOnlyWorkshop', 'RegularPartnerWorkshop'):
            group = SignupGroup.query.filter_by(type=SIGNUP_GROUP_TYPE_PARTNERS). \
                join(group_order_product_mapping). \
                filter_by(order_product_id=self._order_product.id).one_or_none()
            if not group:
                return None
            else:
                partner_order = [op for op in group.order_products if op.id != self._order_product.id][0]
                return OrderProductController(partner_order)
        return None

    @property
    def partner_info(self):
        partner_order_product = self.partner_order_product
        if partner_order_product:
            return MessageController('Partner confirmed: {}'.format(partner_order_product._order_product.registrations[0].name.title()),
                                     status='success', icon='check')
        elif self._order_product.product.type in ('CouplesOnlyWorkshop', 'RegularPartnerWorkshop'):
            token_expiry = self._token_expiry
            if token_expiry:
                if datetime.now() > token_expiry:
                    return [MessageController('No partner.'),
                            MessageController('Your token has expired on {:%d-%b-%Y %H:%M}'.format(token_expiry), icon='info-circle')]
                else:
                    return [MessageController('No partner yet.'),
                            MessageController('Your token for {}:'.format(self._order_product.product.name)),
                            MessageController(self.token, message_type='token'),
                            MessageController('Token expires on {:%d-%b-%Y %H:%M}'.format(token_expiry), status='muted', icon="exclamation-circle")]
            else:
                return [MessageController('No partner yet.'),
                        MessageController('Your token for {}:'.format(self._order_product.product.name)),
                        MessageController(self.token, message_type='token')]
        else:
            return None


class GroupController:
    def __init__(self, order):
        print(order.registration.registration_group_id)
        self._group = order.registration.registration_group

    @property
    def has_group(self):
        return self._group is not None

    @property
    def token(self):
        serialiser = GroupToken()
        return serialiser.serialize(self._group)


    # @property
    # def group_members(self):
    #     for


class OrderSummaryController:
    def __init__(self, order, payment=None):
        self._order = order

        if not payment:
            payment = self._order.payments[0]
        self._payment = payment

    @property
    def transaction_fee(self):
        return self._payment.transaction_fee

    @property
    def total_price(self):
        total_price = self._order.total_price
        return total_price

    @property
    def total_paid(self):
        total_paid = sum([p.amount for p in self._order.payments])
        return total_paid

    @property
    def total_to_pay(self):
        return self._payment.amount + self._payment.transaction_fee

    @property
    def total_transaction_fee(self):
        total_paid = sum([p.transaction_fee for p in self._order.payments])
        return total_paid

    @property
    def total_remaining_amount(self):
        return self.total_price - self.total_paid

    @property
    def show_order_summary(self):
        return len(self._order.order_products.all()) > 0

    @property
    def order_products(self):
        for order_product in self._order.order_products:
            yield OrderProductController(order_product)

    @property
    def payment_items(self):
        for payment_item in self._payment.payment_items:
            yield PaymentItemController(payment_item)

    @property
    def has_waiting_list(self):
        for p in self.order_products:
            if p.is_waiting:
                return True
        return False

    @property
    def event(self):
        return EventController(self._order.event)

    @property
    def token(self):
        return order_serialize(self._order)

    @property
    def order_status_url(self):
        return url_for('event_order_summary',
                       order_token=self.token,
                       _external=True)

    @property
    def invite_partner_url(self):
        tokens = [op.token for op in self.order_products if op.can_add_partner]
        if len(tokens) > 0:
            return url_for('register_form', event_key=self.event.event_key, tokens=','.join(tokens), _external=True)

    @property
    @timestamp_format
    def order_datetime(self):
        return self._order.order_datetime

    def get_waiting_reason(self, order_product):
        if order_product.status == ORDER_PRODUCT_STATUS_WAITING:
            if order_product.product.type == 'CouplesOnlyWorkshop':
                if len([op for op in self._order.order_products if op.product.id==order_product.product.id]) == 1:
                    return 'You are put in the waiting list until your partner signs up'
                else:
                    return 'There are no available places in the workshop'
            return 'You are put on the waiting list due to the current imbalance in leads and followers'

    @property
    def group(self):
        return GroupController(self._order)


class PaymentItemController:
    def __init__(self, payment_item):
        self._payment_item = payment_item

    @property
    def product(self):
        return OrderProductController(self._payment_item.order_product)

    @property
    def amount(self):
        return self._payment_item.amount

class EventController:
    def __init__(self, event):
        self._event = event

    @property
    def name(self):
        return self._event.name

    @property
    def event_key(self):
        return self._event.event_key

    @property
    def registration_url(self):
        return url_for('register_form', event_key=self.event_key, _external=True)



class EventOrderController:
    def __init__(self, event, email, order_products):
        self.email = email
        self._event = event
        self._order_products = order_products

    @classmethod
    def from_email_token(cls, event_key, email_token):
        email = email_deserialize(email_token)
        event = Event.query.filter_by(event_key=event_key).first()
        order_products = cls._get_order_products_for_email(event_key, email)
        return cls(event, email, order_products)

    @staticmethod
    def _get_order_products_for_email(event_key, email):
        order_products = OrderProduct.query. \
                            join(Order, aliased=True).join(Event, aliased=True).filter_by(event_key=event_key). \
                            join(Registration, aliased=True).filter_by(email=email). \
                            all()
        return order_products

    @property
    def order_products(self):
        for order_product in self._order_products:
            yield OrderProductController(order_product)


class FormErrorController:
    def __init__(self, form):
        self._form = form

    @property
    def errors(self):
        for k, v in self._form.errors.items():
            if isinstance(v, dict):
                for k1, v1 in v.items():
                    yield '{}-{}'.format(k, k1), ', '.join(v1)
            else:
                yield k, ', '.join(v)


class MessageController:
    def __init__(self, text, status=None, icon=None, message_type=None):
        self.text = text
        self.status = status
        self.icon = icon
        self.message_type = message_type

    def __repr__(self):
        return self.text

    def __str__(self):
        return self.text

    @property
    def bs_class(self):
        if self.status.lower() in ('success', 'danger', 'warning', 'info', 'muted'):
            return 'text-{}'.format(self.status.lower())