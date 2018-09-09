from salty_tickets.constants import LEADER, FOLLOWER
from salty_tickets.tokens import PartnerToken


def test_e2e_follower_uses_accepted_leaters_token(e2e_vars):
    # stripe will return success
    e2e_vars.mock_stripe.Charge.create.return_value = e2e_vars.sample_stripe_successful_charge

    # LEADER
    leader = e2e_vars.person_factory.pop()

    # checkout
    form_data = {'name': leader.full_name, 'email': leader.email, 'saturday-add': LEADER}
    res = e2e_vars.client.post('/checkout', data=form_data)
    assert res.json['checkout_success']
    leader_payment_id = res.json['payment_id']

    # pay
    res = e2e_vars.client.post('/pay', data={'payment_id': leader_payment_id, 'stripe_token': 'ch_12_leader'})
    assert res.json['success']

    # make sure we have waiting lsit
    event = e2e_vars.dao.get_event_by_key('salty_recipes')
    assert event.products['saturday'].waiting_list.has_waiting_list

    leader = e2e_vars.dao.get_person_by_id(res.json['payee_id'])

    # FOLLOWER
    follower = e2e_vars.person_factory.pop()

    # try without partner, make sure get wait listed
    # price
    form_data = {'name': follower.full_name, 'email': follower.email, 'saturday-add': FOLLOWER}
    res = e2e_vars.client.post('/price', data=form_data)
    assert 25 == res.json['order_summary']['total_price']
    assert [[f'Waiting List: Saturday / Follower / {follower.full_name}', 25.0]] == res.json['order_summary']['items']

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
    assert [[f'Saturday / Follower / {follower.full_name}', 25.0]] == res.json['order_summary']['items']
