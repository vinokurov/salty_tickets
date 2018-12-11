from itsdangerous import URLSafeSerializer, BadSignature
from salty_tickets.config import SECRET_KEY, SALT_EMAIL, SALT_GROUP_TOKEN, \
    SALT_PARTNER_TOKEN, SALT_REGISTRATION_TOKEN
from salty_tickets.dao import TicketsDAO
from hashids import Hashids


def email_serialize(email):
    serializer = URLSafeSerializer(SECRET_KEY, salt=SALT_EMAIL)
    token = serializer.dumps(email)
    return token


def email_deserialize(email_token):
    serializer = URLSafeSerializer(SECRET_KEY, salt=SALT_EMAIL)
    email = serializer.loads(email_token)
    return email


class Token:
    prefix: str = 'tok'
    min_length: int = 5
    salt: str = 'default'

    @property
    def _serializer(self):
        raise NotImplementedError()

    def _encode(self, obj):
        raise NotImplementedError()

    def _decode(self, encoded_data):
        raise NotImplementedError()

    def serialize(self, obj):
        return self.code_to_str(self._encode(self._get_obj_id(obj)))

    def _get_obj_id(self, obj):
        return obj.id

    def deserialize(self, dao: TicketsDAO, token_str):
        token_code = self.code_from_str(token_str)
        decode_res = self._decode(token_code)
        if decode_res:
            id = decode_res
            return self._retrieve_object(dao, id)
        else:
            raise BadSignature('Invalid token')

    def _retrieve_object(self, dao: TicketsDAO, object_id):
        raise NotImplementedError()

    def code_to_str(self, code):
        return f'{self.prefix}_{code}'

    def code_from_str(self, token_str):
        if not token_str.startswith(self.prefix+'_'):
            raise BadSignature('Invalid token')
        token_code = token_str.split(self.prefix+'_')[1]
        return token_code


class ItsdangerousMixin:
    salt = 'default'

    @property
    def _serializer(self):
        return URLSafeSerializer(SECRET_KEY, salt=self.salt)

    def _encode(self, obj):
       return self._serializer.dumps(obj)

    def _decode(self, encoded_data):
        return self._serializer.loads(encoded_data)

    def _get_obj_id(self, obj):
        return str(obj.id)


class HashidsMixin:
    min_length = 5
    salt = 'default'

    def _get_obj_id(self, obj):
        return obj.int_id

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

    def _retrieve_object(self, dao: TicketsDAO, object_id):
        return dao.get_registration_group_by_id(object_id)


class PartnerToken(HashidsMixin, Token):
    """Serialise person id"""
    prefix = 'ptn'
    salt = SALT_PARTNER_TOKEN

    def _retrieve_object(self, dao: TicketsDAO, object_id):
        return dao.get_person_by_id(object_id)


class RegistrationToken(ItsdangerousMixin, Token):
    """Serialise 'registered_by' person id"""
    prefix = 'reg'
    salt = SALT_REGISTRATION_TOKEN

    def _retrieve_object(self, dao: TicketsDAO, object_id):
        return dao.get_person_by_id(object_id)


class PaymentId(ItsdangerousMixin, Token):
    """Serialise payment id"""
    prefix = 'pmt'
    salt = SALT_REGISTRATION_TOKEN

    def _retrieve_object(self, dao: TicketsDAO, object_id):
        return dao.get_payment_by_id(object_id)


class DiscountToken(HashidsMixin, Token):
    """Serialise person id"""
    prefix = 'dsc'
    salt = SALT_PARTNER_TOKEN

    def _retrieve_object(self, dao: TicketsDAO, object_id):
        return dao.get_discount_code_by_id(object_id)

