from datetime import datetime

from itsdangerous import URLSafeSerializer, BadSignature
from salty_tickets.config import SECRET_KEY, SALT_EMAIL, SALT_ORDER_PRODUCT, SALT_ORDER, SALT_GROUP_TOKEN, \
    SALT_PARTNER_TOKEN, SALT_REGISTRATION_TOKEN
from salty_tickets.models import OrderProduct, Order, RegistrationGroup, Registration
from hashids import Hashids


def email_serialize(email):
    serializer =  URLSafeSerializer(SECRET_KEY, salt=SALT_EMAIL)
    token = serializer.dumps(email)
    return token


def email_deserialize(email_token):
    serializer = URLSafeSerializer(SECRET_KEY, salt=SALT_EMAIL)
    email = serializer.loads(email_token)
    return email


def order_product_serialize(order_product):
    serializer =  Hashids(min_length=5, salt=SALT_ORDER_PRODUCT)
    token = serializer.encode(order_product.id)
    return token


def order_product_deserialize(order_product_token):
    # backward compatibility
    if len(order_product_token)>10:
        return order_product_deserialize_old(order_product_token)

    serializer =  Hashids(min_length=5, salt=SALT_ORDER_PRODUCT)
    decode_res = serializer.decode(order_product_token)
    if decode_res:
        order_product_id = decode_res[0]
        order_product = OrderProduct.query.filter_by(id=order_product_id).one()
        return order_product
    else:
        raise BadSignature('Invalid token')


def order_product_token_expired(order_product_token, expire_period_seconds):
    order_product = order_product_deserialize(order_product_token)
    registration_datetime_diff = datetime.now() - order_product.order.order_datetime
    return registration_datetime_diff.total_seconds() > expire_period_seconds


def order_product_deserialize_old(order_product_token):
    serializer =  URLSafeSerializer(SECRET_KEY, salt=SALT_ORDER_PRODUCT)
    order_product_id = serializer.loads(order_product_token)
    order_product = OrderProduct.query.filter_by(id=order_product_id).one()
    return order_product


def order_serialize(user_order):
    serializer =  URLSafeSerializer(SECRET_KEY, salt=SALT_ORDER)
    token = serializer.dumps(user_order.id)
    return token


def order_deserialize(order_token):
    serializer =  URLSafeSerializer(SECRET_KEY, salt=SALT_ORDER)
    order_id = serializer.loads(order_token)
    user_order = Order.query.filter_by(id=order_id).one()
    return user_order



class Token:
    prefix = 'tok'
    min_length = 5
    salt = 'default'
    def __init__(self):
        pass

    @property
    def _serializer(self):
        raise NotImplementedError()

    def _encode(self, obj):
        raise NotImplementedError()

    def _decode(self, encoded_data):
        raise NotImplementedError()

    def serialize(self, obj):
        return '{}_{}'.format(self.prefix, self._encode(obj.id))

    def deserialize(self, token_str):
        if not token_str.startswith(self.prefix+'_'):
            raise BadSignature('Invalid token')
        token_body = token_str.split('_')[1]
        decode_res = self._decode(token_body)
        if decode_res:
            id = decode_res
            return self._retrieve_object(id)
        else:
            raise BadSignature('Invalid token')

    def _retrieve_object(self, id):
        raise NotImplementedError()


class ItsdangerousMixin:
    salt = 'default'

    @property
    def _serializer(self):
        return URLSafeSerializer(SECRET_KEY, salt=self.salt)

    def _encode(self, obj):
       return self._serializer.dumps(obj)

    def _decode(self, encoded_data):
        return self._serializer.loads(encoded_data)


class HashidsMixin:
    min_length = 5
    salt = 'default'

    @property
    def _serializer(self):
        return Hashids(self.salt, self.min_length)

    def _encode(self, obj):
        return self._serializer.encode(obj)

    def _decode(self, encoded_data):
        res = self._serializer.decode(encoded_data)
        if res:
            return res[0]


class GroupToken(HashidsMixin, Token):
    prefix = 'grp'
    salt = SALT_GROUP_TOKEN
    def _retrieve_object(self, id):
        return RegistrationGroup.query.filter_by(id=id).one()


class PartnerToken(HashidsMixin, Token):
    prefix = 'ptn'
    salt = SALT_PARTNER_TOKEN
    def _retrieve_object(self, id):
        return Registration.query.filter_by(id=id).one()


class RegistrationToken(ItsdangerousMixin, Token):
    prefix = 'reg'
    salt = SALT_REGISTRATION_TOKEN
    def _retrieve_object(self, id):
        return Registration.query.filter_by(id=id).one()



