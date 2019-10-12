from salty_tickets.tokens import PartnerToken, RegistrationToken


def test_partner_token(test_dao, salty_recipes, mocker):
    mocker.patch('salty_tickets.tokens.PartnerToken.salt', 'partner_salt')
    event = test_dao.get_event_by_key('salty_recipes', False)
    reg = test_dao.get_registrations_for_ticket(event, 'saturday')[0]
    assert reg.person.int_id is not None

    ptn_token = PartnerToken()
    assert 'partner_salt' == ptn_token.salt
    assert 'ptn_Wlnqr' == ptn_token.serialize(reg.person)


def test_registration_token(test_dao, salty_recipes, mocker):
    mocker.patch('salty_tickets.tokens.RegistrationToken.salt', 'registration_salt')
    event = test_dao.get_event_by_key('salty_recipes', False)
    reg = test_dao.get_registrations_for_ticket(event, 'saturday')[0]
    assert reg.registered_by.int_id is not None

    ptn_token = RegistrationToken()
    assert 'registration_salt' == ptn_token.salt
    reg.registered_by.id = '5bb51f80ab5b8064b088eb27'
    assert 'reg_IjViYjUxZjgwYWI1YjgwNjRiMDg4ZWIyNyI.9jIB1RMzim6ywafiu2r6CFh-qsU' == ptn_token.serialize(reg.registered_by)
