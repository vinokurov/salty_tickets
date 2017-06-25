from datetime import datetime

from itsdangerous import URLSafeSerializer, BadSignature
from salty_tickets.config import SECRET_KEY, SALT_EMAIL, SALT_ORDER_PRODUCT, SALT_ORDER
from salty_tickets.models import OrderProduct, Order
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

