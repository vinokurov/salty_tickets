from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer
from salty_tickets.config import SECRET_KEY


def email_to_token(email):
    serializer =  URLSafeSerializer(SECRET_KEY, salt='email')
    token = serializer.dumps(email)
    return token


def token_to_email(email_token):
    serializer = URLSafeSerializer(SECRET_KEY, salt='email')
    email = serializer.loads(email_token)
    return email

