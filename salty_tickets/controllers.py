from datetime import datetime, timedelta

from flask import url_for
from salty_tickets.models import Event, OrderProduct, Order, Registration, ORDER_PRODUCT_STATUS_WAITING, SignupGroup, \
    SIGNUP_GROUP_TYPE_PARTNERS, group_order_product_mapping
from salty_tickets.products import get_product_by_model
from salty_tickets.tokens import email_deserialize, order_product_serialize, order_product_deserialize, order_serialize


def price_format(func):
    def func_wrap(self):
        return '£{:.2f}'.format(func(self))
    return func_wrap


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
    @price_format
    def price(self):
        return self._order_product.price

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
    def token_expiry(self):
        if self.product_type == 'RegularPartnerWorkshop' and not self.is_waiting:
            return self._order_product.order.order_datetime + timedelta(days=1)
        else:
            return None

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
            return MessageController(partner_order_product._order_product.registrations[0].name.title(),
                                     status='success', icon='check')
        elif self._order_product.product.type in ('CouplesOnlyWorkshop', 'RegularPartnerWorkshop'):
            token_expiry = self.token_expiry
            if token_expiry:
                if datetime.now() > token_expiry:
                    return [MessageController('No partner.'),
                            MessageController('Your token has expired on {:%d-%b-%Y %H:%M}'.format(token_expiry))]
                else:
                    return [MessageController('No partner.'),
                            MessageController('Your token for {}:'.format(self._order_product.product.name)),
                            MessageController(self.token),
                            MessageController('Token expires on {:%d-%b-%Y %H:%M}'.format(token_expiry))]
            else:
                return [MessageController('No partner.'),
                        MessageController('Your token for {}:'.format(self._order_product.product.name)),
                        MessageController(self.token)]
        else:
            return None


class OrderSummaryController:
    def __init__(self, order):
        self._order = order

    @property
    @price_format
    def transaction_fee(self):
        return self._order.transaction_fee

    @property
    @price_format
    def total_price(self):
        total_price = self._order.total_price + self._order.transaction_fee
        return total_price

    @property
    def show_order_summary(self):
        return len(self._order.order_products.all()) > 0

    @property
    def order_products(self):
        for order_product in self._order.order_products:
            yield OrderProductController(order_product)

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

    def get_waiting_reason(self, order_product):
        if order_product.status == ORDER_PRODUCT_STATUS_WAITING:
            if order_product.product.type == 'CouplesOnlyWorkshop':
                if len([op for op in self._order.order_products if op.product.id==order_product.product.id]) == 1:
                    return 'You are put in the waiting list until your partner signs up'
                else:
                    return 'There are no available places in the workshop'
            return 'You are put on the waiting list due to the current imbalance in leads and followers'


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
    def __init__(self, text, status=None, icon=None):
        self.text = text
        self.status = status
        self.icon = icon

    def __repr__(self):
        return self.text

    def __str__(self):
        return self.text

    @property
    def bs_class(self):
        if self.status.lower() in ('success', 'danger', 'warning', 'info'):
            return 'text-{}'.format(self.status.lower())