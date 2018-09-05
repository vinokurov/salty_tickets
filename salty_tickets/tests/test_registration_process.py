from salty_tickets.constants import LEADER, NEW, COUPLE, FOLLOWER
from salty_tickets.forms import create_event_form
from salty_tickets.registration_process import get_payment_from_form


def test_register_one(test_dao, salty_recipes, app, client):

    @app.route('/', methods=['POST'])
    def index():
        event = test_dao.get_event_by_key('salty_recipes')
        form = create_event_form(event)()
        valid = form.validate_on_submit()
        assert valid
        payment = get_payment_from_form(event, form)
        assert [('saturday', LEADER)] == [(r.product_key, r.dance_role) for r in payment.registrations]
        assert ['Saturday / leader / Mr X'] == payment.info_items
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


def test_register_couple(test_dao, salty_recipes, app, client):

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
