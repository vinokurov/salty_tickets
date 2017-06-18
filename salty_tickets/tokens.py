from datetime import datetime

from itsdangerous import URLSafeSerializer
from salty_tickets.config import SECRET_KEY
from salty_tickets.models import OrderProduct


def email_serialize(email):
    serializer =  URLSafeSerializer(SECRET_KEY, salt='email')
    token = serializer.dumps(email)
    return token


def email_deserialize(email_token):
    serializer = URLSafeSerializer(SECRET_KEY, salt='email')
    email = serializer.loads(email_token)
    return email


def order_product_serialize(order_product):
    serializer =  URLSafeSerializer(SECRET_KEY, salt='order_product')
    token = serializer.dumps(order_product.id)
    return token


def order_product_deserialize(order_product_token):
    serializer =  URLSafeSerializer(SECRET_KEY, salt='order_product')
    order_product_id = serializer.loads(order_product_token)
    order_product = OrderProduct.query.filter_by(id=order_product_id).one()
    return order_product


def order_product_token_expired(order_product_token, expire_period_seconds):
    order_product = order_product_deserialize(order_product_token)
    registration_datetime_diff = datetime.now() - order_product.order.order_datetime
    return registration_datetime_diff.total_seconds() > expire_period_seconds

