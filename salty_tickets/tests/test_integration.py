import json

from salty_tickets.constants import LEADER, FOLLOWER, SUCCESSFUL, FAILED
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.registrations import Payment
from salty_tickets.registration_process import PricingResult
from salty_tickets.tokens import PartnerToken


def price(client, form_data, assert_disable_checkout=True) -> dict:
    res = client.post('/price', data=form_data).json
    if assert_disable_checkout:
        assert not res['disable_checkout']
    return res


def checkout(client, form_data, assert_success=True) -> dict:
    res = client.post('/checkout', data=form_data).json
    if assert_success:
        assert res['checkout_success']
    return res


def price_checkout_pay(dao: TicketsDAO, client, form_data, assert_pay_success=True) -> Payment:
    price(client, form_data)
    res = checkout(client, form_data)
    payment_id = res['payment_id']

    # pay
    res = client.post('/pay',
                      data=json.dumps({'payment_id': payment_id,
                                       'stripe_token': {'id': 'ch_12_leader'}}),
                      content_type='application/json')
    if assert_pay_success:
        assert res.json['success']

    return dao.get_payment_by_id(payment_id)


def test_e2e_leader_accepted(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    person = e2e_vars.person_factory.pop()

    # make sure we don't have waiting list for leaders
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.products['saturday'].waiting_list.can_add(LEADER)
    assert not event.products['saturday'].waiting_list.can_add(FOLLOWER)

    form_data = {'name': person.full_name, 'email': person.email, 'saturday-add': LEADER}
    payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data)
    assert not payment.registrations[0].wait_listed
    assert payment.registrations[0].active
    assert 25 == payment.price
    assert SUCCESSFUL == payment.status


def test_e2e_follower_wait_listed(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    person = e2e_vars.person_factory.pop()

    # make sure we have waiting lsit
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.products['saturday'].waiting_list.has_waiting_list

    form_data = {'name': person.full_name, 'email': person.email, 'saturday-add': FOLLOWER}
    payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data)
    assert payment.registrations[0].wait_listed
    assert payment.registrations[0].active
    assert 25 == payment.price
    assert SUCCESSFUL == payment.status


def test_e2e_follower_wait_listed_some(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge
    person = e2e_vars.person_factory.pop()

    # make sure we have waiting list
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.products['saturday'].waiting_list.has_waiting_list
    # make sure we don't  have waiting list on sunday
    assert not event.products['sunday'].waiting_list.has_waiting_list

    form_data = {'name': person.full_name, 'email': person.email,
                 'saturday-add': FOLLOWER, 'sunday-add': FOLLOWER}
    payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data)

    assert payment.registrations[0].wait_listed
    assert payment.registrations[0].active

    assert not payment.registrations[1].wait_listed
    assert payment.registrations[1].active

    assert 50 == payment.price
    assert SUCCESSFUL == payment.status


def test_e2e_follower_uses_accepted_leaders_token(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge

    # LEADER
    leader = e2e_vars.person_factory.pop()
    form_data = {'name': leader.full_name, 'email': leader.email, 'saturday-add': LEADER}
    leader_payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data)
    leader = leader_payment.paid_by

    # make sure we have waiting lsit
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.products['saturday'].waiting_list.has_waiting_list

    # FOLLOWER
    follower = e2e_vars.person_factory.pop()

    # try without partner, make sure get wait listed
    # price
    form_data = {'name': follower.full_name, 'email': follower.email, 'saturday-add': FOLLOWER}
    res = e2e_vars.client.post('/price', data=form_data)
    assert 25 == res.json['order_summary']['total_price']
    expected = [{'dance_role': 'follower',
                 'name': 'Saturday',
                 'partner': None,
                 'person': 'Princess Sande',
                 'price': 25.0,
                 'wait_listed': True}]
    assert expected == res.json['order_summary']['items']

    # Now try with the waiting list
    # TODO get token via api
    ptn_token = PartnerToken().serialize(leader)

    # check token
    res = e2e_vars.client.post('/check_partner_token', data={'partner_token': ptn_token, 'event_key': event.key})
    assert res.json['success']
    assert {'saturday': LEADER} == res.json['roles']
    form_data['partner_token'] = ptn_token

    # checkout with token
    res = e2e_vars.client.post('/price', data=form_data)
    assert 25 == res.json['order_summary']['total_price']
    expected = [{'dance_role': 'follower',
                 'name': 'Saturday',
                 'partner': 'Tammi Speier',     # this is new
                 'person': 'Princess Sande',
                 'price': 25.0,
                 'wait_listed': False}]         # this is new
    assert expected == res.json['order_summary']['items']

    # check that follower gets signed up without waiting list with the token
    follower_payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data)
    assert not follower_payment.registrations[0].wait_listed
    assert follower_payment.registrations[0].active
    assert leader_payment.paid_by == follower_payment.registrations[0].partner

    # check leader is the same
    leader_payment1 = e2e_vars.dao.get_payment_by_id(leader_payment.id)
    assert leader_payment1.registrations[0].active
    assert 25 == leader_payment1.registrations[0].price
    assert not leader_payment1.registrations[0].wait_listed
    assert follower_payment.paid_by == leader_payment1.registrations[0].partner


def test_e2e_leader_uses_waiting_folowers_token(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge

    # make sure we have waiting lsit
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.products['saturday'].waiting_list.has_waiting_list

    # FOLLOWER
    follower = e2e_vars.person_factory.pop()
    form_data = {'name': follower.full_name, 'email': follower.email, 'saturday-add': FOLLOWER}
    follower_payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data)
    assert follower_payment.registrations[0].wait_listed
    assert follower_payment.registrations[0].active
    assert not follower_payment.registrations[0].partner
    assert 25 == follower_payment.registrations[0].price

    # LEADER
    leader = e2e_vars.person_factory.pop()
    form_data = {'name': leader.full_name, 'email': leader.email, 'saturday-add': LEADER}

    # TODO get token via api
    ptn_token = PartnerToken().serialize(follower_payment.paid_by)
    token_res = e2e_vars.client.post('/check_partner_token', data={'partner_token': ptn_token, 'event_key': event.key})
    assert token_res.json['success']
    assert {'saturday': FOLLOWER} == token_res.json['roles']
    form_data['partner_token'] = ptn_token

    # check leader is registered ok
    leader_payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data)
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
    assert event.products['saturday'].waiting_list.has_waiting_list

    # FOLLOWER
    follower = e2e_vars.person_factory.pop()
    form_data = {'name': follower.full_name, 'email': follower.email, 'saturday-add': FOLLOWER}
    follower_payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data)
    assert follower_payment.registrations[0].wait_listed
    assert follower_payment.registrations[0].active
    assert not follower_payment.registrations[0].partner
    assert 25 == follower_payment.registrations[0].price

    # LEADER
    leader = e2e_vars.person_factory.pop()
    form_data = {'name': leader.full_name, 'email': leader.email, 'saturday-add': LEADER}

    # TODO get token via api
    ptn_token = PartnerToken().serialize(follower_payment.paid_by)
    token_res = e2e_vars.client.post('/check_partner_token', data={'partner_token': ptn_token, 'event_key': event.key})
    assert token_res.json['success']
    assert {'saturday': FOLLOWER} == token_res.json['roles']
    form_data['partner_token'] = ptn_token

    # check leader is registered ok
    leader_payment = price_checkout_pay(e2e_vars.dao, e2e_vars.client, form_data, assert_pay_success=False)
    assert FAILED == leader_payment.status
    assert not leader_payment.registrations[0].active
    assert not leader_payment.registrations[0].wait_listed
    assert 25 == leader_payment.registrations[0].price
    assert follower_payment.paid_by == leader_payment.registrations[0].partner

    # refresh follower and check that nothing is changed
    follower_payment1 = e2e_vars.dao.get_payment_by_id(follower_payment.id)
    assert follower_payment.registrations == follower_payment1.registrations
