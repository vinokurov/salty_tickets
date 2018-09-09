import pytest
from mock import patch
from salty_tickets.constants import LEADER, NEW, COUPLE, FOLLOWER, SUCCESSFUL, FAILED
from salty_tickets.dao import PaymentDocument, ProductRegistrationDocument
from salty_tickets.forms import create_event_form
from salty_tickets.models.registrations import ProductRegistration
from salty_tickets.registration_process import get_payment_from_form, do_checkout, do_price, do_pay, \
    do_get_payment_status, PartnerTokenCheckResult, do_check_partner_token
from salty_tickets.tokens import PartnerToken
from salty_tickets.utils.utils import jsonify_dataclass


@pytest.fixture
def sample_data(salty_recipes):
    class SampleData:
        form_data = {
            'name': 'Mr X',
            'email': 'Mr.X@email.com',
            'dance_role': LEADER,
            'partner_name': 'Ms Y',
            'partner_email': 'Ms.Y@email.com',
            'saturday-add': COUPLE,
            'sunday-add': COUPLE,
        }
        pricing_results = {
            'errors': {},
            'stripe': {'amount': 10170, 'email': 'Mr.X@email.com'},
            'order_summary': {
                'total_price': 100.0,
                'transaction_fee': 1.7,
                'total': 101.7,
                'items': [
                    {'name': 'Saturday', 'person': 'Mr X', 'partner': 'Ms Y', 'dance_role': 'leader', 'price': 25.0, 'wait_listed': False},
                    {'name': 'Saturday', 'person': 'Ms Y', 'partner': 'Mr X', 'dance_role': 'follower', 'price': 25.0, 'wait_listed': False},
                    {'name': 'Sunday', 'person': 'Mr X', 'partner': 'Ms Y', 'dance_role': 'leader', 'price': 25.0, 'wait_listed': False},
                    {'name': 'Sunday', 'person': 'Ms Y', 'partner': 'Mr X', 'dance_role': 'follower', 'price': 25.0, 'wait_listed': False},
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
        ProductRegistration(person=p1, dance_role=LEADER, product_key='k1', active=False),
        ProductRegistration(person=p1, product_key='k2', active=True),
        ProductRegistration(person=p1, dance_role=LEADER, product_key='k3', active=True, partner=p2),
    ]
    expected = PartnerTokenCheckResult(success=False, error='Token is not valid for this event')
    assert expected == PartnerTokenCheckResult.from_registration_list(registrations)

    registrations = [
        ProductRegistration(person=p1, dance_role=LEADER, product_key='k1', active=True),
        ProductRegistration(person=p1, dance_role=FOLLOWER, product_key='k2', active=True),
        ProductRegistration(person=p1, dance_role=LEADER, product_key='k3', active=True, partner=p2),
        ProductRegistration(person=p1, dance_role=LEADER, product_key='k4', active=False),
    ]
    expected = PartnerTokenCheckResult(success=True, error='', name=p1.full_name, roles={'k1': LEADER, 'k2': FOLLOWER})
    assert expected == PartnerTokenCheckResult.from_registration_list(registrations)


def test_register_one(test_dao, app, client, salty_recipes):

    @app.route('/', methods=['POST'])
    def index():
        event = test_dao.get_event_by_key('salty_recipes')
        form = create_event_form(event)()
        valid = form.validate_on_submit()
        assert valid
        payment = get_payment_from_form(event, form)
        assert [('saturday', LEADER)] == [(r.product_key, r.dance_role) for r in payment.registrations]
        assert [('Saturday / Leader / Mr X', 25.0)] == payment.info_items
        assert 25 == payment.price
        assert 0.575 == payment.transaction_fee
        assert 'Mr X' == payment.paid_by.full_name
        assert NEW == payment.status
        assert not payment.registrations[0].active
        assert not payment.registrations[0].wait_listed

    post_data = {
        'name': 'Mr X',
        'email': 'Mr.X@email.com',
        'saturday-add': LEADER,
    }
    client.post('/', data=post_data)


def test_register_couple(test_dao, app, client, salty_recipes):

    @app.route('/', methods=['POST'])
    def index():
        event = test_dao.get_event_by_key('salty_recipes')
        form = create_event_form(event)()
        valid = form.validate_on_submit()
        assert valid
        payment = get_payment_from_form(event, form)
        assert [('saturday', LEADER), ('saturday', FOLLOWER),
                ('sunday', LEADER), ('sunday', FOLLOWER)] == [(r.product_key, r.dance_role)
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
    client.post('/', data=post_data)


def test_do_price(test_dao, app_routes, client, sample_data):
    res = client.post('/price', data=sample_data.form_data)

    expected = sample_data.pricing_results.copy()
    expected['checkout_success'] = False
    expected['disable_checkout'] = False
    assert expected == res.json


def test_do_price_validation(test_dao, app_routes, client, sample_data):

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': LEADER}
    res = client.post('/price', data=form_data)
    assert not res.json['errors']
    assert not res.json['disable_checkout']
    assert not res.json['checkout_success']

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com'}
    res = client.post('/price', data=form_data)
    assert not res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']

    form_data = {'name': 'Mr X', 'saturday-add': LEADER}
    res = client.post('/price', data=form_data)
    is_required = ['This field is required.']
    assert {'email': is_required} == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 25 == res.json['order_summary']['total_price']

    form_data = {'saturday-add': LEADER}
    res = client.post('/price', data=form_data)
    is_required = ['This field is required.']
    assert {'email': is_required, 'name': is_required} == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 25 == res.json['order_summary']['total_price']

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': COUPLE}
    res = client.post('/price', data=form_data)

    ptn_required = ['Partner details are required']
    expected_errors = {'dance_role': ptn_required, 'partner_name': ptn_required, 'partner_email': ptn_required}
    assert expected_errors == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 50 == res.json['order_summary']['total_price']


def test_do_checkout(test_dao, app_routes, client, sample_data):
    res = client.post('/checkout', data=sample_data.form_data)

    last_payment = PaymentDocument.objects().order_by('-_id').first()
    sample_data.pricing_results['payment_id'] = str(last_payment.id)

    expected = sample_data.pricing_results.copy()
    expected['checkout_success'] = True
    assert expected == res.json

    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert NEW == payment.status
    for reg in payment.registrations:
        assert not reg.active
        assert not reg.wait_listed


def test_do_checkout_validation(test_dao, app_routes, client, sample_data):

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': LEADER}
    res = client.post('/checkout', data=form_data)
    assert not res.json['errors']
    assert not res.json['disable_checkout']
    assert res.json['checkout_success']

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com'}
    res = client.post('/checkout', data=form_data)
    assert not res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']

    form_data = {'name': 'Mr X', 'saturday-add': LEADER}
    res = client.post('/checkout', data=form_data)
    is_required = ['This field is required.']
    assert {'email': is_required} == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 25 == res.json['order_summary']['total_price']

    form_data = {'saturday-add': LEADER}
    res = client.post('/checkout', data=form_data)
    is_required = ['This field is required.']
    assert {'email': is_required, 'name': is_required} == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 25 == res.json['order_summary']['total_price']

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': COUPLE}
    res = client.post('/checkout', data=form_data)

    ptn_required = ['Partner details are required']
    expected_errors = {'dance_role': ptn_required, 'partner_name': ptn_required, 'partner_email': ptn_required}
    assert expected_errors == res.json['errors']
    assert res.json['disable_checkout']
    assert not res.json['checkout_success']
    assert 50 == res.json['order_summary']['total_price']


def test_do_pay_success(mock_stripe, sample_stripe_successful_charge, test_dao, app_routes, client, sample_data):
    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge

    client.post('/checkout', data=sample_data.form_data)
    last_payment = PaymentDocument.objects().order_by('-_id').first()

    post_data = {'payment_id': str(last_payment.id), 'stripe_token': 'ch_test'}
    res = client.post('/pay', data=post_data)

    expected = {'success': True, 'error_message': None, 'payee_id': str(last_payment.paid_by.id),
                'payment_id': str(last_payment.id), 'complete': True}
    assert expected == res.json
    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert SUCCESSFUL == payment.status
    for reg in payment.registrations:
        assert reg.active
        assert not reg.wait_listed

    # try do_pay on the same payment, make sure we receive an error
    res = client.post('/pay', data=post_data)
    assert not res.json['success']
    assert res.json['error_message']


def test_do_pay_failure(mock_stripe, sample_stripe_card_error, test_dao, app_routes, client, sample_data):
    mock_stripe.Charge.create.side_effect = sample_stripe_card_error

    client.post('/checkout', data=sample_data.form_data)
    last_payment = PaymentDocument.objects().order_by('-_id').first()

    post_data = {'payment_id': str(last_payment.id), 'stripe_token': 'ch_test'}
    res = client.post('/pay', data=post_data)

    expected = {'success': False, 'error_message': 'Sample card error',
                'payee_id': None, 'payment_id': str(last_payment.id), 'complete': True}
    assert expected == res.json
    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert FAILED == payment.status
    assert sample_stripe_card_error.json_body == payment.stripe.charge
    for reg in payment.registrations:
        assert not reg.active
        assert not reg.wait_listed


def test_do_pay_failure_then_success(mock_stripe, sample_stripe_card_error, sample_stripe_successful_charge,
                                     test_dao, app_routes, client, sample_data):
    # first CardError, then success
    mock_stripe.Charge.create.side_effect = [sample_stripe_card_error, sample_stripe_successful_charge]

    client.post('/checkout', data=sample_data.form_data)
    last_payment = PaymentDocument.objects().order_by('-_id').first()

    post_data = {'payment_id': str(last_payment.id), 'stripe_token': 'ch_test'}
    res = client.post('/pay', data=post_data)

    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert FAILED == payment.status

    post_data = {'payment_id': str(last_payment.id), 'stripe_token': 'ch_test'}
    res = client.post('/pay', data=post_data)

    expected = {'success': True, 'error_message': None, 'payee_id': str(last_payment.paid_by.id),
                'payment_id': str(last_payment.id), 'complete': True}
    assert expected == res.json
    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert SUCCESSFUL == payment.status
    for reg in payment.registrations:
        assert reg.active
        assert not reg.wait_listed


def test_registration_process_balance(mock_stripe, sample_stripe_successful_charge,
                                     test_dao, app_routes, client, sample_data, salty_recipes):

    event = test_dao.get_event_by_key('salty_recipes')
    assert event.products['saturday'].waiting_list.has_waiting_list
    saturday_reg_stat = event.products['saturday'].waiting_list.registration_stats

    followers_number = saturday_reg_stat[FOLLOWER].accepted
    leaders_number = saturday_reg_stat[LEADER].accepted
    ratio = event.products['saturday'].ratio

    leads_to_add = 3
    # check the event set up. After adding {leads_to_add} leaders the auto balancing should get triggered
    assert (followers_number + 1) / (leaders_number + leads_to_add - 1) > ratio
    assert (followers_number + 1) / (leaders_number + leads_to_add) <= ratio
    assert (leaders_number + leads_to_add) / followers_number <= ratio

    first_waiting_follower = [doc for key, doc in salty_recipes.registration_docs.items()
                              if doc.wait_listed and doc.dance_role == FOLLOWER and doc.active][0]
    assert first_waiting_follower

    names = ['Antwan', 'Otto', 'Cruz', 'Genaro', 'Adalberto']

    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    for leader_name in names[:leads_to_add]:
        first_waiting_follower.reload()
        assert first_waiting_follower.wait_listed

        form_data = {'name': leader_name, 'email': f'{leader_name}@email.com', 'saturday-add': LEADER}
        res = client.post('/checkout', data=form_data)

        post_data = {'payment_id': res.json['payment_id'], 'stripe_token': 'ch_test'}
        res = client.post('/pay', data=post_data)
        assert res.json['success']

    first_waiting_follower.reload()
    assert not first_waiting_follower.wait_listed


def test_do_get_payment_status(mock_stripe, sample_stripe_card_error, sample_stripe_successful_charge,
                               test_dao, app_routes, client, sample_data):

    form_data = {'name': 'Mr X', 'email': f'Mr.X@email.com', 'saturday-add': LEADER}
    res = client.post('/checkout', data=form_data)
    payment_id = res.json['payment_id']

    # payment hasn't been initiated yet
    post_data = {'payment_id': payment_id, 'stripe_token': 'ch_test'}
    res = client.post('/payment_status', data=post_data)
    expected = {
        'complete': False,
        'error_message': 'Payment not initiated yet',
        'payee_id': None,
        'payment_id': None,
        'success': False
    }
    assert expected == res.json

    mock_stripe.Charge.create.side_effect = [sample_stripe_card_error, sample_stripe_successful_charge]
    # payment was failed
    post_data = {'payment_id': payment_id, 'stripe_token': 'ch_test'}
    res = client.post('/pay', data=post_data)
    assert not res.json['success']
    assert res.json['complete']

    # wrong stripe token
    post_data = {'payment_id': payment_id, 'stripe_token': 'ch_test_aaaaa'}
    res = client.post('/payment_status', data=post_data)
    expected = {
        'complete': True,
        'error_message': 'Access denied to see payment status',
        'payee_id': None,
        'payment_id': None,
        'success': False
    }
    assert expected == res.json

    # now get the failed payment details
    post_data = {'payment_id': payment_id, 'stripe_token': 'ch_test'}
    res = client.post('/payment_status', data=post_data)
    expected = {
        'complete': True,
        'error_message': 'Sample card error',
        'payee_id': None,
        'payment_id': payment_id,
        'success': False
    }
    assert expected == res.json

    # complete payment
    post_data = {'payment_id': payment_id, 'stripe_token': 'ch_test'}
    res = client.post('/pay', data=post_data)
    assert res.json['success']
    assert res.json['complete']
    payee_id = res.json['payee_id']

    # now get the succeeded payment details
    post_data = {'payment_id': payment_id, 'stripe_token': 'ch_test'}
    res = client.post('/payment_status', data=post_data)
    expected = {
        'complete': True,
        'error_message': None,
        'payee_id': payee_id,
        'payment_id': payment_id,
        'success': True
    }
    assert expected == res.json


def test_do_check_partner_token(salty_recipes, test_dao, app_routes, client):
    partner = test_dao.get_registrations_for_product('salty_recipes', 'saturday')[0].person
    ptn_token = PartnerToken().serialize(partner)
    post_data = {'partner_token': ptn_token, 'event_key': 'salty_recipes'}
    res = client.post('/check_partner_token', data=post_data)

    expected = {'success': True, 'error': '', 'name': partner.full_name,
                'roles': {'saturday': LEADER, 'sunday': LEADER}}
    assert expected == res.json

    partner = salty_recipes.registration_docs[('Stevie Stumpf', 'sunday', True)].to_dataclass().person
    ptn_token = PartnerToken().serialize(partner)
    post_data = {'partner_token': ptn_token, 'event_key': 'salty_recipes'}
    res = client.post('/check_partner_token', data=post_data)
    assert res.json['error']
    assert not res.json['roles']
    assert not res.json['success']
