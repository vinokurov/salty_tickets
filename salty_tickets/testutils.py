import json

from salty_tickets.dao import TicketsDAO
from salty_tickets.models.registrations import Payment


def post_json_data(client, url, data):
    return client.post(url, data=json.dumps(data), content_type='application/json')


def process_test_price(client, form_data, assert_disable_checkout=True) -> dict:
    res = post_json_data(client, '/price', form_data).json
    if assert_disable_checkout:
        assert not res['disable_checkout']
    return res


def process_test_checkout(client, form_data, assert_success=True) -> dict:
    res = post_json_data(client, '/checkout', form_data).json
    if assert_success:
        assert res['checkout_success']
    return res


def process_pay(assert_success, client, stripe_token='ch_test'):
    res = post_json_data(client, '/pay', {'stripe_token': {'id': stripe_token}})
    if assert_success:
        assert res.json['success']
    return res


def process_test_price_checkout_pay(dao: TicketsDAO, client, form_data, assert_pay_success=True) -> Payment:
    process_test_price(client, form_data)
    res = process_test_checkout(client, form_data)
    res = process_pay(assert_pay_success, client, stripe_token='ch_12_leader')

    payment_id = res.json['payment_id']

    return dao.get_payment_by_id(payment_id) if payment_id else None


