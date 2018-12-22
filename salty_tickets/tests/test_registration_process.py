import json
import pickle

import pytest
from salty_tickets.constants import LEADER, NEW, COUPLE, FOLLOWER, SUCCESSFUL, FAILED
from salty_tickets.dao import PaymentDocument, PersonDocument
from salty_tickets.forms import create_event_form
from salty_tickets.models.registrations import Registration, Payment, PaymentStripeDetails
from salty_tickets.api.registration_process import get_payment_from_form, PartnerTokenCheckResult, process_first_payment
from salty_tickets.testutils import post_json_data
from salty_tickets.tokens import PartnerToken, PaymentId


@pytest.fixture
def sample_data(salty_recipes):
    class SampleData:
        form_data = {
            'name': 'Mr X',
            'email': 'Mr.X@email.com',
            'location': {
                "city": "London",
                "state_district": "Greater London",
                "state": "England",
                "postcode": "SW1A 2DU",
                "country": "United Kingdom",
                "country_code": "gb",
                "query": "London"
            },
            'dance_role': LEADER,
            'partner_name': 'Ms Y',
            'partner_email': 'Ms.Y@email.com',
            'partner_location': {
                "city": "London",
                "state_district": "Greater London",
                "state": "England",
                "postcode": "SW1A 2DU",
                "country": "United Kingdom",
                "country_code": "gb",
                "query": "London"
            },
            'saturday-add': COUPLE,
            'sunday-add': COUPLE,
            'pay_all': 'y',
        }
        pricing_results = {
            'errors': {},
            'stripe': {'amount': 10170, 'email': 'Mr.X@email.com'},
            'order_summary': {
                'pay_all_now': True,
                'pay_now': 100.0,
                'pay_now_fee': 1.7,
                'pay_now_total': 101.7,
                'total_price': 100.0,
                'transaction_fee': 1.7,
                'total': 101.7,
                'items': [
                    {'name': 'Saturday', 'key': 'saturday', 'person': 'Mr X', 'partner': 'Ms Y', 'dance_role': 'leader', 'price': 25.0, 'wait_listed': False},
                    {'name': 'Saturday', 'key': 'saturday', 'person': 'Ms Y', 'partner': 'Mr X', 'dance_role': 'follower', 'price': 25.0, 'wait_listed': False},
                    {'name': 'Sunday', 'key': 'sunday', 'person': 'Mr X', 'partner': 'Ms Y', 'dance_role': 'leader', 'price': 25.0, 'wait_listed': False},
                    {'name': 'Sunday', 'key': 'sunday', 'person': 'Ms Y', 'partner': 'Mr X', 'dance_role': 'follower', 'price': 25.0, 'wait_listed': False},
                ]},
            'disable_checkout': False,
            'checkout_success': False,
            'payment_id': '',
        }
    return SampleData()


def test_PartnerTokenCheckResult(test_dao, person_factory):
    p1 = person_factory.pop()
    p2 = person_factory.pop()

    expected = PartnerTokenCheckResult(success=False, error='Token is not valid for this event')
    assert expected == PartnerTokenCheckResult.from_registration_list([])

    registrations = [
        Registration(person=p1, dance_role=LEADER, ticket_key='k1', active=False),
        Registration(person=p1, ticket_key='k2', active=True),
        Registration(person=p1, dance_role=LEADER, ticket_key='k3', active=True, partner=p2),
    ]
    expected = PartnerTokenCheckResult(success=False, error='Token is not valid for this event')
    assert expected == PartnerTokenCheckResult.from_registration_list(registrations)

    registrations = [
        Registration(person=p1, dance_role=LEADER, ticket_key='k1', active=True),
        Registration(person=p1, dance_role=FOLLOWER, ticket_key='k2', active=True),
        Registration(person=p1, dance_role=LEADER, ticket_key='k3', active=True, partner=p2),
        Registration(person=p1, dance_role=LEADER, ticket_key='k4', active=False),
    ]
    expected = PartnerTokenCheckResult(success=True, error='', name=p1.full_name, roles={'k1': LEADER, 'k2': FOLLOWER})
    assert expected == PartnerTokenCheckResult.from_registration_list(registrations)


def test_register_one(test_dao, app, client, salty_recipes):

    post_data = {
        'name': 'Mr X',
        'email': 'Mr.X@email.com',
        'saturday-add': LEADER,
        'location': {
            "city": "London",
            "state_district": "Greater London",
            "state": "England",
            "postcode": "SW1A 2DU",
            "country": "United Kingdom",
            "country_code": "gb",
            "query": "London"
        },
    }

    @app.route('/', methods=['POST'])
    def index():
        event = test_dao.get_event_by_key('salty_recipes')
        form = create_event_form(event)()
        valid = form.validate_on_submit()
        assert valid
        payment = get_payment_from_form(event, form)
        assert [('saturday', LEADER)] == [(r.ticket_key, r.dance_role) for r in payment.registrations]
        assert [('Saturday / Leader / Mr X', 25.0)] == payment.info_items
        assert 25 == payment.price
        assert 0.57 == payment.transaction_fee
        assert 'Mr X' == payment.paid_by.full_name
        assert post_data['location'] == payment.paid_by.location
        assert post_data['location'] == payment.registrations[0].person.location
        assert post_data['location'] == payment.registrations[0].registered_by.location
        assert NEW == payment.status
        assert not payment.registrations[0].active
        assert not payment.registrations[0].wait_listed

    post_json_data(client, '/', post_data)


def test_register_couple(test_dao, app, client, salty_recipes):

    @app.route('/', methods=['POST'])
    def index():
        event = test_dao.get_event_by_key('salty_recipes')
        form = create_event_form(event)()
        valid = form.validate_on_submit()
        assert valid
        payment = get_payment_from_form(event, form)
        assert [('saturday', LEADER), ('saturday', FOLLOWER),
                ('sunday', LEADER), ('sunday', FOLLOWER)] == [(r.ticket_key, r.dance_role)
                                                              for r in payment.registrations]
        # assert ['Saturday / leader / Mr X'] == payment.info_items
        assert 100 == payment.price
        assert 1.7 == payment.transaction_fee
        assert 'Mr X' == payment.paid_by.full_name
        assert 'Mr X' == payment.registrations[0].person.full_name
        assert 'Mr X' == payment.registrations[0].registered_by.full_name
        assert 'Ms Y' == payment.registrations[0].partner.full_name
        assert 'Ms Y' == payment.registrations[1].person.full_name
        assert 'Mr X' == payment.registrations[1].partner.full_name
        assert 'Mr X' == payment.registrations[1].registered_by.full_name
        assert NEW == payment.status
        assert not payment.registrations[0].active
        assert not payment.registrations[0].wait_listed

    post_data = {
        'name': 'Mr X',
        'email': 'Mr.X@email.com',
        'dance_role': LEADER,
        'partner_name': 'Ms Y',
        'partner_email': 'Ms.Y@email.com',
        'saturday-add': COUPLE,
        'sunday-add': COUPLE,
    }
    post_json_data(client, '/', post_data)


def test_do_price(test_dao, app_routes, client, sample_data):
    res = post_json_data(client, '/price', sample_data.form_data)

    expected = sample_data.pricing_results.copy()
    expected['new_prices'] = [{'ticket_key': 'party', 'price': 10}]
    expected['checkout_success'] = False
    expected['disable_checkout'] = False
    assert expected == res.json


def test_do_price_validation(test_dao, app_routes, client, sample_data):

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': LEADER}
    res = post_json_data(client, '/price', data=form_data)
    assert not res.json['errors']
    assert not res.json['disable_checkout']
    assert not res.json['checkout_success']

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com'}
    res = post_json_data(client, '/price', data=form_data)
    assert not res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']

    form_data = {'name': 'Mr X', 'saturday-add': LEADER}
    res = post_json_data(client, '/price', data=form_data)
    is_required = ['This field is required.']
    assert {'email': is_required} == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 25 == res.json['order_summary']['total_price']

    form_data = {'saturday-add': LEADER}
    res = post_json_data(client, '/price', data=form_data)
    is_required = ['This field is required.']
    assert {'email': is_required, 'name': is_required} == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 25 == res.json['order_summary']['total_price']

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': COUPLE}
    res = post_json_data(client, '/price', data=form_data)

    ptn_required = ['Partner details are required']
    expected_errors = {'dance_role': ptn_required, 'partner_name': ptn_required, 'partner_email': ptn_required}
    assert expected_errors == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 50 == res.json['order_summary']['total_price']


def test_do_checkout(test_dao, app_routes, client, sample_data):
    res = post_json_data(client, '/checkout', data=sample_data.form_data)

    expected = sample_data.pricing_results.copy()
    expected['payment_id'] = ''
    expected['checkout_success'] = True
    expected['new_prices'] = [{'ticket_key': 'party', 'price': 10}]
    assert expected == res.json

    # payment is saved in the session
    with client.session_transaction() as sess:
        payment = pickle.loads(sess.get('payment'))
        assert 'salty_recipes' == sess.get('event_key')
    assert payment is not None
    assert NEW == payment.status
    for reg in payment.registrations:
        assert not reg.active
        assert not reg.wait_listed


def test_do_checkout_validation(test_dao, app_routes, client, sample_data):

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': LEADER}
    res = post_json_data(client, '/checkout', data=form_data)
    assert not res.json['errors']
    assert not res.json['disable_checkout']
    assert res.json['checkout_success']

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com'}
    res = post_json_data(client, '/checkout', data=form_data)
    assert not res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']

    form_data = {'name': 'Mr X', 'saturday-add': LEADER}
    res = post_json_data(client, '/checkout', data=form_data)
    is_required = ['This field is required.']
    assert {'email': is_required} == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 25 == res.json['order_summary']['total_price']

    form_data = {'saturday-add': LEADER}
    res = post_json_data(client, '/checkout', data=form_data)
    is_required = ['This field is required.']
    assert {'email': is_required, 'name': is_required} == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 25 == res.json['order_summary']['total_price']

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': COUPLE}
    res = post_json_data(client, '/checkout', data=form_data)

    ptn_required = ['Partner details are required']
    expected_errors = {'dance_role': ptn_required, 'partner_name': ptn_required, 'partner_email': ptn_required}
    assert expected_errors == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 50 == res.json['order_summary']['total_price']


def test_do_pay_success(mock_send_email, mock_stripe, sample_stripe_successful_charge, test_dao, app_routes, client, sample_data):
    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    assert 0 == PersonDocument.objects(full_name=sample_data.form_data['name']).count()

    res = post_json_data(client, '/checkout', data=sample_data.form_data)
    with client.session_transaction() as sess:
        payment = sess.get('payment')
        assert payment is not None

    res = post_pay(client)
    last_payment = PaymentDocument.objects().order_by('-_id').first()
    pmt_token = PaymentId().serialize(last_payment)

    expected = {'success': True, 'error_message': None, 'payee_id': str(last_payment.paid_by.id),
                'pmt_token': pmt_token, 'payment_id': str(last_payment.id), 'complete': True}
    assert expected == res.json
    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert SUCCESSFUL == payment.status
    assert payment.price == payment.paid_price

    for reg in payment.registrations:
        assert reg.active
        assert not reg.wait_listed

    with client.session_transaction() as sess:
        assert sess.get('payment') is None
        assert sess.get('event_key') is None

    # make sure that person is added only once
    assert 1 == PersonDocument.objects(full_name=sample_data.form_data['name']).count()

    # try do_pay on the same payment, make sure we receive an error
    res = post_pay(client)
    assert not res.json['success']
    assert res.json['error_message']


def post_pay(client, stripe_token_id='ch_test', url='/pay'):
    post_data = {'stripe_token': {'id': stripe_token_id}}
    res = client.post(url, data=json.dumps(post_data), content_type='application/json')
    return res


def post_payment_status(client, payment_id, stripe_token_id='ch_test', url='/payment_status'):
    post_data = {'payment_id': str(payment_id), 'stripe_token': {'id': stripe_token_id}}
    res = client.post(url, data=json.dumps(post_data), content_type='application/json')
    return res


def test_do_pay_failure(mock_send_email, mock_stripe, sample_stripe_card_error, test_dao, app_routes, client, sample_data):
    mock_stripe.Charge.create.side_effect = sample_stripe_card_error

    post_json_data(client, '/checkout', data=sample_data.form_data)

    res = post_pay(client)
    last_payment = PaymentDocument.objects().order_by('-_id').first()

    expected = {'success': False, 'error_message': 'Payment has been declined by the provider.', 'pmt_token': None,
                'payee_id': None, 'payment_id': str(last_payment.id), 'complete': True}
    assert expected == res.json
    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert FAILED == payment.status
    for reg in payment.registrations:
        assert not reg.active
        assert not reg.wait_listed

    with client.session_transaction() as sess:
        assert sess.get('payment') is not None
        assert sess.get('event_key') is not None


def test_do_pay_failure_then_success(mock_send_email, mock_stripe, sample_stripe_card_error, sample_stripe_successful_charge,
                                     test_dao, app_routes, client, sample_data):
    # first CardError, then success
    mock_stripe.Charge.create.side_effect = [sample_stripe_card_error, sample_stripe_successful_charge]

    post_json_data(client, '/checkout', data=sample_data.form_data)

    res = post_pay(client)
    assert not res.json['success']
    last_payment = PaymentDocument.objects().order_by('-_id').first()

    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert FAILED == payment.status

    res = post_pay(client)
    pmt_token = PaymentId().serialize(last_payment)

    expected = {'success': True, 'error_message': None, 'payee_id': str(last_payment.paid_by.id),
                'pmt_token': pmt_token, 'payment_id': str(last_payment.id), 'complete': True}
    assert expected == res.json
    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert SUCCESSFUL == payment.status
    for reg in payment.registrations:
        assert reg.active
        assert not reg.wait_listed

    with client.session_transaction() as sess:
        assert sess.get('payment') is None
        assert sess.get('event_key') is None


def test_registration_process_balance(mock_send_email, mock_stripe, sample_stripe_successful_charge, sample_stripe_customer,
                                     test_dao, app_routes, client, sample_data, salty_recipes, person_factory):

    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    mock_stripe.Customer.create.return_value = sample_stripe_customer

    event = test_dao.get_event_by_key('salty_recipes')
    assert not event.tickets['sunday'].waiting_list.has_waiting_list

    def _register_one(role):
        person = person_factory.pop()
        form_data = {'name': person.full_name, 'email': person.email, 'sunday-add': role}
        post_json_data(client, '/checkout', data=form_data)
        res = post_pay(client)
        assert res.json['success']
        return res

    # add followers so that we have a waiting list
    while not event.tickets['sunday'].waiting_list.has_waiting_list:
        res = _register_one(FOLLOWER)
        event = test_dao.get_event_by_key('salty_recipes')

    first_waiting_follower_payment_id = res.json['payment_id']
    first_waiting_follower = test_dao.get_payment_by_id(first_waiting_follower_payment_id).registrations[0]
    assert not first_waiting_follower.is_paid

    # now create leaders until we can balance
    waiting_list = event.tickets['sunday'].waiting_list
    while waiting_list.registration_stats[FOLLOWER].accepted / (waiting_list.registration_stats[LEADER].accepted + 1) > waiting_list.ratio:
        _register_one(LEADER)
        first_waiting_follower = test_dao.get_payment_by_id(first_waiting_follower_payment_id).registrations[0]
        assert first_waiting_follower.wait_listed

        event = test_dao.get_event_by_key('salty_recipes')
        waiting_list = event.tickets['sunday'].waiting_list

    # now add one more leader and make sure that waiting list gets balanced
    _register_one(LEADER)
    event = test_dao.get_event_by_key('salty_recipes')
    waiting_list = event.tickets['sunday'].waiting_list

    assert waiting_list.current_ratio <= waiting_list.ratio
    follower_payment = test_dao.get_payment_by_id(first_waiting_follower_payment_id)
    first_waiting_follower = follower_payment.registrations[0]
    assert not first_waiting_follower.wait_listed
    assert [(25, True)] == [(t.price, t.success) for t in follower_payment.transactions]
    assert 25 == follower_payment.paid_price


def test_do_get_payment_status(mock_send_email, mock_stripe, sample_stripe_card_error, sample_stripe_successful_charge,
                               test_dao, app_routes, client, sample_data):

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': LEADER}
    res = post_json_data(client, '/checkout', data=form_data)
    # payment_id = res.json['payment_id']

    mock_stripe.Charge.create.side_effect = [sample_stripe_card_error, sample_stripe_successful_charge]
    # payment was failed
    res = post_pay(client, stripe_token_id='ch_test')
    assert not res.json['success']
    assert res.json['complete']

    with client.session_transaction() as sess:
        payment = pickle.loads(sess.get('payment'))
        payment_id = str(payment.id)

    # wrong stripe token
    res = post_payment_status(client, payment_id, stripe_token_id='ch_test_aaaaa')
    expected = {
        'complete': True,
        'error_message': 'Access denied to see payment status',
        'payee_id': None,
        'pmt_token': None,
        'payment_id': None,
        'success': False
    }
    assert expected == res.json

    # now get the failed payment details
    res = post_payment_status(client, payment_id, stripe_token_id='ch_test')

    expected = {
        'complete': True,
        'error_message': 'Payment failed',
        'payee_id': None,
        'pmt_token': None,
        'payment_id': payment_id,
        'success': False
    }
    assert expected == res.json

    # complete payment
    res = post_pay(client, stripe_token_id='ch_test')
    assert res.json['success']
    assert res.json['complete']
    payee_id = res.json['payee_id']

    # now get the succeeded payment details
    res = post_payment_status(client, payment_id, stripe_token_id='ch_test')
    pmt_token = PaymentId().serialize(payment)
    expected = {
        'complete': True,
        'error_message': None,
        'pmt_token': pmt_token,
        'payee_id': payee_id,
        'payment_id': payment_id,
        'success': True
    }
    assert expected == res.json


def test_do_check_partner_token(mock_send_email, salty_recipes, test_dao, app_routes, client):
    event = test_dao.get_event_by_key('salty_recipes', False)
    partner = test_dao.get_registrations_for_ticket(event, 'saturday')[0].person
    ptn_token = PartnerToken().serialize(partner)
    post_data = {'partner_token': ptn_token, 'event_key': 'salty_recipes'}
    res = post_json_data(client, '/check_partner_token', data=post_data)

    expected = {'success': True, 'error': '', 'name': partner.full_name,
                'roles': {'saturday': LEADER, 'sunday': LEADER}}
    assert expected == res.json

    partner = salty_recipes.registration_docs[('Stevie Stumpf', 'sunday', True)].to_dataclass().person
    ptn_token = PartnerToken().serialize(partner)
    post_data = {'partner_token': ptn_token, 'event_key': 'salty_recipes'}
    res = post_json_data(client, '/check_partner_token', data=post_data)
    assert res.json['error']
    assert not res.json['roles']
    assert not res.json['success']


def test_process_first_payment(mock_send_email, mock_stripe, sample_stripe_card_error, sample_stripe_successful_charge,
                               sample_stripe_customer, person_factory):
    psn = person_factory.pop()

    def _payment_from_registrations(registrations, pay_all_now=True):
        price = sum([r.price or 0 for r in registrations] or [0])
        if pay_all_now:
            first_pay = price
        else:
            first_pay = sum([r.price or 0 for r in registrations if not r.wait_listed] or [0])
        payment = Payment(paid_by=psn, registrations=registrations, price=price,
                          pay_all_now=pay_all_now, first_pay_amount=first_pay,
                          stripe=PaymentStripeDetails(token_id='tok_123'))
        payment.id = 'abc123'
        return payment

    # Pay now, all accepted, stripe - OK
    payment = _payment_from_registrations([
        Registration(registered_by=psn, person=psn, price=25),
        Registration(registered_by=psn, person=psn, price=25),
        Registration(registered_by=psn, person=psn),
    ], pay_all_now=True)

    mock_stripe.Charge.create.side_effect = [sample_stripe_successful_charge]
    assert process_first_payment(payment)
    assert 50 == payment.paid_price
    assert [True, True, True] == [r.is_paid for r in payment.registrations]
    assert [(50, True)] == [(t.price, t.success) for t in payment.transactions]
    assert SUCCESSFUL == payment.status

    # Pay now, all accepted, stripe - charge ERROR
    payment = _payment_from_registrations([
        Registration(registered_by=psn, person=psn, price=25),
        Registration(registered_by=psn, person=psn, price=25),
    ], pay_all_now=True)

    mock_stripe.Charge.create.side_effect = [sample_stripe_card_error]
    assert not process_first_payment(payment)
    assert not payment.paid_price
    assert [False, False] == [r.is_paid for r in payment.registrations]
    assert [(50, False)] == [(t.price, t.success) for t in payment.transactions]
    assert payment.transactions[0].error_response
    assert FAILED == payment.status

    # Pay later, but all accepted, stripe - OK
    payment = _payment_from_registrations([
        Registration(registered_by=psn, person=psn, price=25),
        Registration(registered_by=psn, person=psn, price=25),
    ], pay_all_now=False)

    mock_stripe.Charge.create.side_effect = [sample_stripe_successful_charge]
    mock_stripe.Customer.create.side_effect = [sample_stripe_customer]
    assert process_first_payment(payment)
    assert 50 == payment.paid_price
    assert [True, True] == [r.is_paid for r in payment.registrations]
    assert [(50, True)] == [(t.price, t.success) for t in payment.transactions]
    assert SUCCESSFUL == payment.status

    # Pay now, one wait listed, stripe - OK
    payment = _payment_from_registrations([
        Registration(registered_by=psn, person=psn, price=25),
        Registration(registered_by=psn, person=psn, price=25, wait_listed=True),
        Registration(registered_by=psn, person=psn),
    ], pay_all_now=True)

    mock_stripe.Charge.create.side_effect = [sample_stripe_successful_charge]
    mock_stripe.Customer.create.side_effect = [sample_stripe_customer]
    assert process_first_payment(payment)
    assert 50 == payment.paid_price
    assert [True, True, True] == [r.is_paid for r in payment.registrations]
    assert [(50, True)] == [(t.price, t.success) for t in payment.transactions]
    assert SUCCESSFUL == payment.status

    # Pay later, one wait listed, stripe - OK
    payment = _payment_from_registrations([
        Registration(registered_by=psn, person=psn, price=25),
        Registration(registered_by=psn, person=psn, price=25, wait_listed=True),
        Registration(registered_by=psn, person=psn),
    ], pay_all_now=False)

    mock_stripe.Charge.create.side_effect = [sample_stripe_successful_charge]
    mock_stripe.Customer.create.side_effect = [sample_stripe_customer]
    assert process_first_payment(payment)
    assert 25 == payment.paid_price
    assert [True, False, True] == [r.is_paid for r in payment.registrations]
    assert [(25, True)] == [(t.price, t.success) for t in payment.transactions]
    assert SUCCESSFUL == payment.status

    # Pay later, all wait listed, stripe - OK
    payment = _payment_from_registrations([
        Registration(registered_by=psn, person=psn, price=25, wait_listed=True),
        Registration(registered_by=psn, person=psn, price=25, wait_listed=True),
    ], pay_all_now=False)

    mock_stripe.Charge.create.side_effect = [sample_stripe_successful_charge]
    mock_stripe.Customer.create.side_effect = [sample_stripe_customer]
    assert process_first_payment(payment)
    assert 0 == payment.paid_price
    assert [False, False] == [r.is_paid for r in payment.registrations]
    assert [] == [(t.price, t.success) for t in payment.transactions]
    assert SUCCESSFUL == payment.status

    # Pay later, one wait listed, stripe - charge failure
    payment = _payment_from_registrations([
        Registration(registered_by=psn, person=psn, price=25, wait_listed=False),
        Registration(registered_by=psn, person=psn, price=25, wait_listed=True),
    ], pay_all_now=False)

    mock_stripe.Charge.create.side_effect = [sample_stripe_card_error]
    mock_stripe.Customer.create.side_effect = [sample_stripe_customer]
    assert not process_first_payment(payment)
    assert not payment.paid_price
    assert [False, False] == [r.is_paid for r in payment.registrations]
    assert [(25, False)] == [(t.price, t.success) for t in payment.transactions]
    assert FAILED == payment.status

    # Pay later, one wait listed, stripe - customer failure
    payment = _payment_from_registrations([
        Registration(registered_by=psn, person=psn, price=25, wait_listed=True),
        Registration(registered_by=psn, person=psn, price=25, wait_listed=True),
    ], pay_all_now=False)

    mock_stripe.Charge.create.side_effect = [sample_stripe_successful_charge]
    mock_stripe.Customer.create.side_effect = [sample_stripe_card_error]
    assert not process_first_payment(payment)
    assert not payment.paid_price
    assert [False, False] == [r.is_paid for r in payment.registrations]
    assert [] == [(t.price, t.success) for t in payment.transactions]
    assert FAILED == payment.status

