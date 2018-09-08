import pytest
from mock import patch
from salty_tickets.constants import LEADER, NEW, COUPLE, FOLLOWER, SUCCESSFUL
from salty_tickets.dao import PaymentDocument
from salty_tickets.forms import create_event_form
from salty_tickets.registration_process import get_payment_from_form, do_checkout, do_price, do_pay


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
                    ['Saturday / Leader / Mr X', 25.0],
                    ['Saturday / Follower / Ms Y', 25.0],
                    ['Sunday / Leader / Mr X', 25.0],
                    ['Sunday / Follower / Ms Y', 25.0],
                ]},
            'disable_checkout': True,
            'checkout_success': False,
            'payment_id': '',
        }
    return SampleData()


@pytest.fixture
def app_routes(app, test_dao):
    @app.route('/price', methods=['POST'])
    def _price():
        return do_price(test_dao, 'salty_recipes')

    @app.route('/checkout', methods=['POST'])
    def _checkout():
        return do_checkout(test_dao, 'salty_recipes')

    @app.route('/pay', methods=['POST'])
    def _pay():
        return do_pay(test_dao)


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
        assert NEW == payment.registrations[0].status

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
        assert NEW == payment.registrations[0].status

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
    assert sample_data.pricing_results == res.json


def test_do_checkout(test_dao, app_routes, client, sample_data):
    res = client.post('/checkout', data=sample_data.form_data)

    last_payment = PaymentDocument.objects().order_by('-_id').first()
    sample_data.pricing_results['payment_id'] = str(last_payment.id)
    assert sample_data.pricing_results == res.json

    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert NEW == payment.status
    for reg in payment.registrations:
        assert not reg.active


@patch('salty_tickets.registration_process.stripe_charge')
def test_do_pay_success(mock_stripe_charge, test_dao, app_routes, client, sample_data):
    # mock stripe_charge to return success
    def _stripe_charge(_payment):
        _payment.status = SUCCESSFUL
        return True
    mock_stripe_charge.side_effect = _stripe_charge

    client.post('/checkout', data=sample_data.form_data)
    last_payment = PaymentDocument.objects().order_by('-_id').first()

    post_data = {'payment_id': str(last_payment.id), 'stripe_token': 'ch_test'}
    res = client.post('/pay', data=post_data)

    assert {'success': True, 'error_message': None, 'payee_id': str(last_payment.paid_by.id)} == res.json
    payment = test_dao.get_payment_by_id(str(last_payment.id))
    assert SUCCESSFUL == payment.status
    for reg in payment.registrations:
        assert reg.active

    # try do_pay on the same payment, make sure we receive an error
    res = client.post('/pay', data=post_data)
    assert not res.json['success']
    assert res.json['error_message']


