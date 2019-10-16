from salty_tickets.constants import LEADER, FOLLOWER, SUCCESSFUL, FAILED
from salty_tickets.testutils import process_test_price_checkout_pay
from salty_tickets.tokens import PartnerToken


def test_e2e_leader_accepted(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    person = e2e_vars.person_factory.pop()

    # make sure we don't have waiting list for leaders
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.can_add(LEADER)
    assert not event.tickets['saturday'].waiting_list.can_add(FOLLOWER)

    form_data = {'name': person.full_name, 'email': person.email, 'saturday-add': LEADER}
    payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    assert not payment.registrations[0].wait_listed
    assert payment.registrations[0].active
    assert 25 == payment.price
    assert SUCCESSFUL == payment.status


def test_e2e_follower_wait_listed_pay_all(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    person = e2e_vars.person_factory.pop()

    # make sure we have waiting lsit
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.has_waiting_list

    form_data = {'name': person.full_name, 'email': person.email, 'saturday-add': FOLLOWER, 'pay_all': 'y'}
    payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    assert payment.registrations[0].wait_listed
    assert payment.registrations[0].active
    assert payment.registrations[0].is_paid
    assert 25 == payment.price
    assert 25 == payment.paid_price
    assert SUCCESSFUL == payment.status


def test_e2e_follower_wait_listed_some_pay_all(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    person = e2e_vars.person_factory.pop()

    # make sure we have waiting list
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.has_waiting_list
    # make sure we don't  have waiting list on sunday
    assert not event.tickets['sunday'].waiting_list.has_waiting_list

    form_data = {'name': person.full_name, 'email': person.email, 'pay_all': 'y',
                 'saturday-add': FOLLOWER, 'sunday-add': FOLLOWER}
    payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)

    assert payment.registrations[0].wait_listed
    assert payment.registrations[0].active
    assert payment.registrations[0].is_paid

    assert not payment.registrations[1].wait_listed
    assert payment.registrations[1].active
    assert payment.registrations[1].is_paid

    assert 50 == payment.price
    assert 50 == payment.paid_price
    assert SUCCESSFUL == payment.status


def test_e2e_follower_wait_listed_pay_later(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    e2e_vars.mock_stripe.Customer.create.return_value = e2e_vars.sample_stripe_customer
    person = e2e_vars.person_factory.pop()

    # make sure we have waiting lsit
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.has_waiting_list

    form_data = {'name': person.full_name, 'email': person.email, 'saturday-add': FOLLOWER, 'pay_all': ''}
    payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    assert payment.registrations[0].wait_listed
    assert payment.registrations[0].active
    assert not payment.registrations[0].is_paid
    assert 25 == payment.price
    assert 0 == payment.paid_price
    assert SUCCESSFUL == payment.status


def test_e2e_follower_wait_listed_some_pay_later(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    e2e_vars.mock_stripe.Customer.create.return_value = e2e_vars.sample_stripe_customer
    person = e2e_vars.person_factory.pop()

    # make sure we have waiting list
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.has_waiting_list
    # make sure we don't  have waiting list on sunday
    assert not event.tickets['sunday'].waiting_list.has_waiting_list

    form_data = {'name': person.full_name, 'email': person.email, 'pay_all': '',
                 'saturday-add': FOLLOWER, 'sunday-add': FOLLOWER}
    payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)

    assert payment.registrations[0].wait_listed
    assert payment.registrations[0].active
    assert not payment.registrations[0].is_paid

    assert not payment.registrations[1].wait_listed
    assert payment.registrations[1].active
    assert payment.registrations[1].is_paid

    assert 50 == payment.price
    assert 25 == payment.paid_price
    assert SUCCESSFUL == payment.status


def test_e2e_follower_uses_accepted_leaders_token(e2e_vars):
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge

    # LEADER
    leader = e2e_vars.person_factory.pop()
    form_data = {'name': leader.full_name, 'email': leader.email, 'saturday-add': LEADER}
    leader_payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    leader = leader_payment.paid_by

    # make sure we have waiting lsit
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.has_waiting_list

    # FOLLOWER
    new_client = e2e_vars.app.test_client()
    follower = e2e_vars.person_factory.pop()

    # try without partner, make sure get wait listed
    # price
    form_data = {'name': follower.full_name, 'email': follower.email, 'saturday-add': FOLLOWER}
    res = new_client.post(f'/price/{event.key}', data=form_data)
    assert 25 == res.json['order_summary']['total_price']
    expected = [{'dance_role': 'follower',
                 'name': 'Saturday',
                 'key': 'saturday',
                 'partner': None,
                 'person': 'Princess Sande',
                 'price': 25.0,
                 'wait_listed': True}]
    assert expected == res.json['order_summary']['items']

    # Now try with the waiting list
    # TODO get token via api
    ptn_token = PartnerToken().serialize(leader)

    # check token
    res = new_client.post('/check_partner_token', data={'partner_token': ptn_token, 'event_key': event.key})
    assert res.json['success']
    assert {'saturday': LEADER} == res.json['roles']
    form_data['partner_token'] = ptn_token

    # checkout with token
    res = new_client.post(f'/price/{event.key}', data=form_data)
    assert 25 == res.json['order_summary']['total_price']
    expected = [{'dance_role': 'follower',
                 'name': 'Saturday',
                 'key': 'saturday',
                 'partner': 'Tammi Speier',     # this is new
                 'person': 'Princess Sande',
                 'price': 25.0,
                 'wait_listed': False}]         # this is new
    assert expected == res.json['order_summary']['items']

    # check that follower gets signed up without waiting list with the token
    follower_payment = process_test_price_checkout_pay(e2e_vars.dao, new_client, event.key, form_data)
    assert not follower_payment.registrations[0].wait_listed
    assert follower_payment.registrations[0].active
    assert leader_payment.paid_by == follower_payment.registrations[0].partner

    # check leader is the same
    leader_payment1 = e2e_vars.dao.get_payment_by_id(leader_payment.id)
    assert leader_payment1.registrations[0].active
    assert 25 == leader_payment1.registrations[0].price
    assert not leader_payment1.registrations[0].wait_listed
    assert follower_payment.paid_by == leader_payment1.registrations[0].partner


def test_e2e_leader_uses_waiting_followers_token(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge

    # make sure we have waiting list
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.has_waiting_list

    # FOLLOWER
    follower = e2e_vars.person_factory.pop()
    form_data = {'name': follower.full_name, 'email': follower.email, 'pay_all': 'y', 'saturday-add': FOLLOWER}
    follower_payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    assert follower_payment.registrations[0].wait_listed
    assert follower_payment.registrations[0].active
    assert not follower_payment.registrations[0].partner
    assert 25 == follower_payment.registrations[0].price

    # LEADER
    leader = e2e_vars.person_factory.pop()
    form_data = {'name': leader.full_name, 'email': leader.email, 'pay_all': 'y', 'saturday-add': LEADER}

    # TODO get token via api
    ptn_token = PartnerToken().serialize(follower_payment.paid_by)
    token_res = e2e_vars.client.post('/check_partner_token', data={'partner_token': ptn_token, 'event_key': event.key})
    assert token_res.json['success']
    assert {'saturday': FOLLOWER} == token_res.json['roles']
    form_data['partner_token'] = ptn_token

    # check leader is registered ok
    leader_payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    assert not leader_payment.registrations[0].wait_listed
    assert leader_payment.registrations[0].active
    assert 25 == leader_payment.registrations[0].price
    assert follower_payment.paid_by == leader_payment.registrations[0].partner

    # refresh follower and check that the follower info has been updated
    follower_payment = e2e_vars.dao.get_payment_by_id(follower_payment.id)
    assert follower_payment.registrations[0].active
    assert 25 == follower_payment.registrations[0].price
    assert not follower_payment.registrations[0].wait_listed
    assert leader_payment.paid_by == follower_payment.registrations[0].partner


def test_e2e_leader_uses_waiting_folowers_token_but_payment_fails(e2e_vars):
    # stripe will return success, then card error
    e2e_vars.mock_stripe.Charge.create.side_effect = [e2e_vars.sample_stripe_successful_charge,
                                                      e2e_vars.sample_stripe_card_error]

    # make sure we have waiting lsit
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.has_waiting_list

    # FOLLOWER
    follower = e2e_vars.person_factory.pop()
    form_data = {'name': follower.full_name, 'email': follower.email, 'pay_all': 'y', 'saturday-add': FOLLOWER}
    follower_payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    assert follower_payment.registrations[0].wait_listed
    assert follower_payment.registrations[0].active
    assert not follower_payment.registrations[0].partner
    assert 25 == follower_payment.registrations[0].price
    assert follower_payment.registrations[0].is_paid
    assert follower_payment.price == follower_payment.paid_price

    # LEADER
    leader = e2e_vars.person_factory.pop()
    form_data = {'name': leader.full_name, 'email': leader.email, 'saturday-add': LEADER}

    # TODO get token via api
    ptn_token = PartnerToken().serialize(follower_payment.paid_by)
    token_res = e2e_vars.client.post('/check_partner_token', data={'partner_token': ptn_token, 'event_key': event.key})
    assert token_res.json['success']
    assert {'saturday': FOLLOWER} == token_res.json['roles']
    form_data['partner_token'] = ptn_token

    # check leader yayment is saved with success=FALSE
    leader_payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data, assert_pay_success=False)
    assert FAILED == leader_payment.status
    assert not leader_payment.registrations[0].active
    assert not leader_payment.registrations[0].wait_listed
    assert 25 == leader_payment.registrations[0].price
    assert follower_payment.paid_by == leader_payment.registrations[0].partner

    # refresh follower and check that nothing is changed
    follower_payment1 = e2e_vars.dao.get_payment_by_id(follower_payment.id)
    assert follower_payment.registrations == follower_payment1.registrations


def test_e2e_follower_pays_later_leader_uses_her_token(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    e2e_vars.mock_stripe.Customer.create.return_value = e2e_vars.sample_stripe_customer

    # make sure we have waiting list
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.tickets['saturday'].waiting_list.has_waiting_list

    # FOLLOWER
    follower = e2e_vars.person_factory.pop()
    form_data = {'name': follower.full_name, 'email': follower.email, 'pay_all': '', 'saturday-add': FOLLOWER}
    follower_payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    assert follower_payment.registrations[0].wait_listed
    assert follower_payment.registrations[0].active
    assert not follower_payment.registrations[0].partner
    assert 25 == follower_payment.registrations[0].price

    assert 0 == follower_payment.paid_price
    assert 25 == follower_payment.price

    # LEADER
    leader = e2e_vars.person_factory.pop()
    form_data = {'name': leader.full_name, 'email': leader.email, 'pay_all': 'y', 'saturday-add': LEADER}

    # TODO get token via api
    ptn_token = PartnerToken().serialize(follower_payment.paid_by)
    token_res = e2e_vars.client.post('/check_partner_token', data={'partner_token': ptn_token, 'event_key': event.key})
    assert token_res.json['success']
    assert {'saturday': FOLLOWER} == token_res.json['roles']
    form_data['partner_token'] = ptn_token

    # check leader is registered ok
    leader_payment = process_test_price_checkout_pay(e2e_vars.dao, e2e_vars.client, event.key, form_data)
    assert not leader_payment.registrations[0].wait_listed
    assert leader_payment.registrations[0].active
    assert 25 == leader_payment.registrations[0].price
    assert follower_payment.paid_by == leader_payment.registrations[0].partner

    # refresh follower and check that the follower info has been updated
    follower_payment = e2e_vars.dao.get_payment_by_id(follower_payment.id)
    assert follower_payment.registrations[0].active
    assert 25 == follower_payment.registrations[0].price
    assert not follower_payment.registrations[0].wait_listed
    assert leader_payment.paid_by == follower_payment.registrations[0].partner
