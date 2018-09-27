from mock import patch
from salty_tickets.tokens import PartnerToken, RegistrationToken


@patch('salty_tickets.tokens.PartnerToken.salt', 'partner_salt')
def test_partner_token(test_dao, salty_recipes):
    reg = test_dao.get_registrations_for_product('salty_recipes', 'saturday')[0]
    assert reg.person.int_id is not None

    ptn_token = PartnerToken()
    assert 'partner_salt' == ptn_token.salt
    assert 'ptn_Wlnqr' == ptn_token.serialize(reg.person)


@patch('salty_tickets.tokens.RegistrationToken.salt', 'registration_salt')
def test_registration_token(test_dao, salty_recipes):
    reg = test_dao.get_registrations_for_product('salty_recipes', 'saturday')[0]
    assert reg.registered_by.int_id is not None

    ptn_token = RegistrationToken()
    assert 'registration_salt' == ptn_token.salt
    assert 'reg_MQ.tJOtcIErHNyInNaXHYDeRa8Di2A' == ptn_token.serialize(reg.registered_by)
