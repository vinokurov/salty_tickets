from datetime import datetime

import pytest
from salty_tickets.api.registration_process import do_price, do_checkout, do_pay, do_get_payment_status, \
    do_check_partner_token, do_create_registration_group, do_validate_registration_group_token, \
    do_validate_discount_code_token
from salty_tickets.constants import LEADER, COUPLE
from salty_tickets.models.discounts import GroupDiscountProduct, FixedValueDiscountProduct, CodeDiscountProduct
from salty_tickets.models.event import Event
from salty_tickets.models.registrations import DiscountCode
from salty_tickets.models.tickets import WorkshopTicket, PartyTicket, FestivalPassTicket
from salty_tickets.models.products import Product
from salty_tickets.testutils import process_test_price_checkout_pay, post_json_data, process_test_price
from salty_tickets.tokens import GroupToken, DiscountToken, RegistrationToken
from salty_tickets.utils.utils import jsonify_dataclass


@pytest.fixture
def mts(test_dao):
    event = Event(
        name='Mind the Shag 2019',
        key='mind_the_shag_2019',
        start_date=datetime(2019, 3, 29, 19, 0),
        end_date=datetime(2019, 3, 31, 23, 0),
        info='Mind the Shag - London Shag Festival',
        pricing_rules=[
            {
                "name": "mind_the_shag",
                "kwargs": {
                    "price_station": 30.0,
                    "price_clinic": 40.0,
                    "price_station_extra": 25.0,
                }
            },
            {
                'name': 'tagged_base',
                'kwargs': {'tag': 'pass'}
            },
            {
                'name': 'tagged_base',
                'kwargs': {'tag': 'party'}
            },
        ],
        validation_rules=[
            {
                "name": "non_overlapping",
                "kwargs": {
                    "tag": "station",
                    "error_text": "Workshops shouldn't overlap in time."
                }
            }
        ],
    )

    kwargs_station = dict(
        ratio=1.5,
        allow_first=5,
        max_available=30,
        base_price=27.5,
        tags={'station'}
    )

    kwargs_train = dict(
        ratio=1.5,
        allow_first=5,
        max_available=30,
        base_price=27.5,
        tags={'station', 'train'}
    )

    tickets = [
        WorkshopTicket(
            name='Rockabilly Bopper Shag',
            key='rockabilly_bopper',
            info='Rockabilly Bopper Shag info',
            start_datetime=datetime(2019, 3, 30, 11, 0),
            end_datetime=datetime(2019, 3, 30, 13, 0),
            teachers='Patrick & Fancy',
            level='collegiate any',
            **kwargs_station,
        ),
        WorkshopTicket(
            name='St.Louis Cocktail',
            key='stl_cocktail',
            info='St.Louis Cocktail info',
            start_datetime=datetime(2019, 3, 30, 11, 0),
            end_datetime=datetime(2019, 3, 30, 13, 0),
            teachers='Rokas & Simona',
            level='St.Louis Any',
            **kwargs_station,
        ),
        WorkshopTicket(
            name='Showmans Shag',
            key='showmans_shag',
            info='Showmans Shag info',
            start_datetime=datetime(2019, 3, 30, 14, 0),
            end_datetime=datetime(2019, 3, 30, 16, 0),
            teachers='Partick & Fancy',
            level='Collegiate Adv',
            **kwargs_station,
        ),
        WorkshopTicket(
            name='Shag Boomerang',
            key='shag_boomerang',
            info='Shag Boomerang info',
            start_datetime=datetime(2019, 3, 30, 14, 0),
            end_datetime=datetime(2019, 3, 30, 16, 0),
            teachers='Teis & Maja',
            level='Collegiate Any',
            **kwargs_station,
        ),
        WorkshopTicket(
            name='Hurricane Shag',
            key='hurricane_shag',
            info='Hurricane Shag info',
            start_datetime=datetime(2019, 3, 30, 16, 30),
            end_datetime=datetime(2019, 3, 30, 18, 30),
            teachers='Filip & Cherry',
            level='Collegiate Any',
            **kwargs_station,
        ),
        WorkshopTicket(
            name='Shag ABC',
            key='shag_abc',
            info='Shag Roots info',
            start_datetime=datetime(2019, 3, 30, 11, 0),
            end_datetime=datetime(2019, 3, 30, 13, 0),
            teachers='Filip & Cherry',
            level='Collegiate Beginner',
            **kwargs_train,
        ),
        WorkshopTicket(
            name='Shag Essentials',
            key='shag_essentials',
            info='Rising Shag info',
            start_datetime=datetime(2019, 3, 30, 14, 0),
            end_datetime=datetime(2019, 3, 30, 16, 0),
            teachers='Filip & Cherry',
            level='Collegiate Beginner',
            **kwargs_train,
        ),
        WorkshopTicket(
            name='Shag Clinic',
            key='shag_clinic',
            info='Shag Clinic info',
            start_datetime=datetime(2019, 3, 30, 16, 30),
            end_datetime=datetime(2019, 3, 30, 18, 30),
            teachers='various teachers',
            level='Collegiate Advanced',
            ratio=1.0,
            allow_first=1,
            max_available=12,
            base_price=40.0,
            tags={'mts', 'station', 'clinic'},
        ),
        WorkshopTicket(
            name='Shag Roller Coaster',
            key='shag_roller_coaster',
            info='Shag Roller Coaster info',
            start_datetime=datetime(2019, 3, 31, 11, 0),
            end_datetime=datetime(2019, 3, 31, 13, 0),
            teachers='Filip & Cherry',
            level='Collegiate Any',
            **kwargs_station,
        ),
        PartyTicket(
            name='Friday Party',
            key='friday_party',
            info='Friday Party Info',
            start_datetime=datetime(2019, 3, 29, 20, 0),
            end_datetime=datetime(2019, 3, 30, 2, 0),
            location='Limehouse Townhall',
            base_price=25.0,
            max_available=200,
            tags={'party'},
        ),
        PartyTicket(
            name='Saturday Party',
            key='saturday_party',
            info='Saturday Party Info',
            start_datetime=datetime(2019, 3, 30, 20, 0),
            end_datetime=datetime(2019, 3, 31, 2, 0),
            location='Limehouse Townhall',
            base_price=25.0,
            max_available=200,
            tags={'party'},
        ),
        PartyTicket(
            name='Sunday Party',
            key='sunday_party',
            info='Sunday Party Info',
            start_datetime=datetime(2019, 3, 31, 20, 0),
            end_datetime=datetime(2019, 3, 31, 23, 0),
            location='JuJus Bar & Stage',
            base_price=15.0,
            max_available=150,
            tags={'party'},
        ),
        FestivalPassTicket(
            name='Full Pass',
            key='full_pass',
            info='Includes 3 stations and all parties',
            base_price=120.0,
            tags={'pass', 'includes_parties', 'station_discount_3', 'group_discount', 'overseas_discount'},
        ),
        FestivalPassTicket(
            name='Shag Novice Track',
            key='shag_novice',
            info='Intensive beginner shag training and all parties',
            base_price=90.0,
            tags={'pass', 'includes_parties', 'station_discount_2', 'group_discount', 'overseas_discount'},
        ),
        FestivalPassTicket(
            name='Shag Novice Track w/o parties',
            key='shag_novice_no_parties',
            info='Intensive beginner shag and no parties',
            base_price=45.0,
            tags={'pass', 'station_discount_2'},
        ),
        FestivalPassTicket(
            name='Party Pass',
            key='party_pass',
            info='Includes all 3 parties',
            base_price=55.0,
            tags={'pass', 'includes_parties'},
        ),
    ]

    products = [
        Product(
            name='Tote bag',
            key='tote_bag',
            tags={'merchandise'},
            base_price=5.0,
            options={
                'blue': 'Navy Blue',
                'red': 'Burgundy Red',
            }
        ),
        Product(
            name='T-shirt',
            key='tshirt',
            tags={'merchandise'},
            base_price=20.0,
            options={
                'male_s': 'Male (S)',
                'male_m': 'Male (M)',
                'male_l': 'Male (L)',
                'male_xl': 'Male (XL)',
                'female_xs': 'Female (XS)',
                'female_s': 'Female (S)',
                'female_m': 'Female (M)',
                'female_l': 'Female (L)',
            }
        ),
        Product(
            name='Bottle',
            key='bottle',
            tags={'merchandise'},
            base_price=5.0,
            options={
                'blue': 'Navy Blue',
            }
        ),
    ]

    discount_products = [
        GroupDiscountProduct(
            name='Group Discount',
            info='Group Discount',
            discount_value=10,
            tag='group_discount',
        ),
        FixedValueDiscountProduct(
            name='Overseas Discount',
            info='Overseas Discount',
            discount_value=20,
            tag='overseas_discount',
        ),
        CodeDiscountProduct(
            name='Discount Code',
            info='Discount Code',
        )
    ]

    event.append_tickets(tickets)
    event.append_products(products)
    event.append_discount_products(discount_products)
    test_dao.create_event(event)
    return event


@pytest.fixture
def mts_app_routes(app, test_dao):
    event_key = 'mind_the_shag_2019'

    @app.route('/price', methods=['POST'])
    def _price():
        return jsonify_dataclass(do_price(test_dao, event_key))

    @app.route('/checkout', methods=['POST'])
    def _checkout():
        return jsonify_dataclass(do_checkout(test_dao, event_key))

    @app.route('/pay', methods=['POST'])
    def _pay():
        return jsonify_dataclass(do_pay(test_dao))

    @app.route('/payment_status', methods=['POST'])
    def _payment_status():
        return jsonify_dataclass(do_get_payment_status(test_dao))

    @app.route('/check_partner_token', methods=['POST'])
    def _check_partner_token():
        return jsonify_dataclass(do_check_partner_token(test_dao))

    @app.route('/check_discount_token', methods=['POST'])
    def _check_discount_token():
        return jsonify_dataclass(do_validate_discount_code_token(test_dao, event_key))

    @app.route('/check_registration_group_token', methods=['POST'])
    def _check_registration_group_token():
        return jsonify_dataclass(do_validate_registration_group_token(test_dao, event_key))

    @app.route('/create_registration_group', methods=['POST'])
    def _create_registration_group():
        return jsonify_dataclass(do_create_registration_group(test_dao, event_key))

    @app.route('/admin_create_discount_code', methods=['POST'])
    def _admin_create_discount_code():
        pass


def test_full_pass_registration_solo(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                     sample_stripe_card_error, sample_stripe_successful_charge,
                                     sample_stripe_customer, mock_send_email):
    # stripe will return success
    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'full_pass-add': LEADER,
        'rockabilly_bopper-add': LEADER,
        'showmans_shag-add': LEADER,
        'hurricane_shag-add': LEADER,
        'friday_party-add': LEADER,
        'saturday_party-add': LEADER,
        'sunday_party-add': LEADER,
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 120.0 == payment.price


def test_full_pass_registration_couple(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                       sample_stripe_card_error, sample_stripe_successful_charge,
                                       sample_stripe_customer, mock_send_email):
    # stripe will return success
    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    partner = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'full_pass-add': COUPLE,
        'rockabilly_bopper-add': COUPLE,
        'showmans_shag-add': COUPLE,
        'hurricane_shag-add': COUPLE,
        'friday_party-add': COUPLE,
        'saturday_party-add': COUPLE,
        'sunday_party-add': COUPLE,
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 240.0 == payment.price


def test_full_pass_with_estras_registration_solo(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                     sample_stripe_card_error, sample_stripe_successful_charge,
                                     sample_stripe_customer, mock_send_email):
    # stripe will return success
    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'full_pass-add': LEADER,
        'rockabilly_bopper-add': LEADER,
        'shag_roller_coaster-add': LEADER,
        'showmans_shag-add': LEADER,
        'hurricane_shag-add': LEADER,
        'friday_party-add': LEADER,
        'saturday_party-add': LEADER,
        'sunday_party-add': LEADER,
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 145.0 == payment.price


def test_full_pass_with_clinic_registration_couple(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                       sample_stripe_card_error, sample_stripe_successful_charge,
                                       sample_stripe_customer, mock_send_email):
    # stripe will return success
    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    partner = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'full_pass-add': COUPLE,
        'rockabilly_bopper-add': COUPLE,
        'showmans_shag-add': COUPLE,
        'shag_clinic-add': COUPLE,
        'friday_party-add': COUPLE,
        'saturday_party-add': COUPLE,
        'sunday_party-add': COUPLE,
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 270.0 == payment.price


def test_full_pass_registration_couple_with_products(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                       sample_stripe_card_error, sample_stripe_successful_charge,
                                       sample_stripe_customer, mock_send_email):
    # stripe will return success
    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    partner = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'full_pass-add': COUPLE,
        'rockabilly_bopper-add': COUPLE,
        'showmans_shag-add': COUPLE,
        'hurricane_shag-add': COUPLE,
        'friday_party-add': COUPLE,
        'saturday_party-add': COUPLE,
        'sunday_party-add': COUPLE,
        'tshirt-add': {'male_l': 1, 'female_s': 1},
        'bottle-add': {'blue': 2}
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 290.0 == payment.price
    assert 50 == sum([p.price for p in payment.purchases])


def test_registration_with_overseas_discount(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                       sample_stripe_card_error, sample_stripe_successful_charge,
                                       sample_stripe_customer, mock_send_email):
    # stripe will return success
    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    partner = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'full_pass-add': COUPLE,
        'rockabilly_bopper-add': COUPLE,
        'showmans_shag-add': COUPLE,
        'hurricane_shag-add': COUPLE,
        'friday_party-add': COUPLE,
        'saturday_party-add': COUPLE,
        'sunday_party-add': COUPLE,
        'tshirt-add': {'male_l': 1, 'female_s': 1},
        'bottle-add': {'blue': 2},
        'overseas_discount-validated': 'checked',
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 240 == sum([p.price for p in payment.registrations])
    assert 50 == sum([p.price for p in payment.purchases])
    assert 40 == sum([p.value for p in payment.discounts])
    assert 240 + 50 - 40 == payment.price

    # no discount if no full pass
    person = person_factory.pop()
    partner = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'rockabilly_bopper-add': COUPLE,
        'showmans_shag-add': COUPLE,
        'overseas_discount-validated': 'checked',
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 120 == payment.price
    assert 120 == sum([p.price for p in payment.registrations])
    assert not [p.price for p in payment.purchases]
    assert not [p.value for p in payment.discounts]

    # partner doesn't have full pass
    person = person_factory.pop()
    partner = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'full_pass-add': LEADER,
        'rockabilly_bopper-add': LEADER,
        'showmans_shag-add': LEADER,
        'hurricane_shag-add': COUPLE,
        'friday_party-add': LEADER,
        'saturday_party-add': LEADER,
        'sunday_party-add': COUPLE,
        'tshirt-add': {'male_l': 1, 'female_s': 1},
        'bottle-add': {'blue': 2},
        'overseas_discount-validated': 'checked',
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 120 + 30 + 15 == sum([p.price for p in payment.registrations])
    assert 50 == sum([p.price for p in payment.purchases])
    assert 20 == sum([p.value for p in payment.discounts])
    assert 120 + 30 + 15 + 50 - 20 == payment.price


def test_validate_registration_group(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                     sample_stripe_card_error, sample_stripe_successful_charge,
                                     sample_stripe_customer, mock_send_email):
    res = post_json_data(client, '/create_registration_group', {
        'name': 'My Group',
        'location': {"city": "Cardiff", "country": "United Kingdom", "country_code": "gb"},
        'email': 'test@gmail.com',
    })
    assert res.json['success']
    token = res.json['token']
    assert token
    assert len(token) < 10

    res = post_json_data(client, '/check_registration_group_token', {
        'name': 'Mr.X',
        'location': {"city": "Cardiff", "country": "United Kingdom", "country_code": "gb"},
        'email': 'test@gmail.com',
        'group_discount-code': token,
    })
    assert res.json['success']
    assert 'My Group' == res.json['info']

    # same country, different city - OK
    res = post_json_data(client, '/check_registration_group_token', {
        'name': 'Mr.X',
        'location': {"city": "London", "country": "United Kingdom", "country_code": "gb"},
        'email': 'test@gmail.com',
        'group_discount-code': token,
    })
    assert res.json['success']

    # wrong token
    res = post_json_data(client, '/check_registration_group_token', {
        'name': 'Mr.X',
        'location': {"city": "Cardiff", "country": "United Kingdom", "country_code": "gb"},
        'email': 'test@gmail.com',
        'group_discount-code': 'wrong',
    })
    assert not res.json['success']

    # disfferent country - not OK
    res = post_json_data(client, '/check_registration_group_token', {
        'name': 'Mr.X',
        'location': {"city": "Eindhoven", "country": "Netherlands", "country_code": "nl"},
        'email': 'test@gmail.com',
        'group_discount-code': token,
    })
    assert not res.json['success']


def test_registration_with_a_group(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                   sample_stripe_card_error, sample_stripe_successful_charge,
                                   sample_stripe_customer, mock_send_email):
    res = post_json_data(client, '/create_registration_group', {
        'name': 'My Group',
        'location': {"city": "Cardiff", "country": "United Kingdom", "country_code": "gb"},
        'email': 'test@gmail.com',
    })
    group_token = res.json['token']
    group = GroupToken().deserialize(test_dao, group_token)
    assert not group.admin
    assert not group.members
    assert 'gb' == group.location['country_code']

    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'full_pass-add': LEADER,
        'rockabilly_bopper-add': LEADER,
        'showmans_shag-add': LEADER,
        'hurricane_shag-add': LEADER,
        'friday_party-add': LEADER,
        'saturday_party-add': LEADER,
        'sunday_party-add': LEADER,
        'group_discount-code': group_token,
        'group_discount-validated': 'yes',
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None

    assert 10 == payment.discounts[0].value
    group = GroupToken().deserialize(test_dao, group_token)
    expected_members = [payment.paid_by]
    assert expected_members == group.members

    # trying to use group key, but don't have a full pass
    person = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'showmans_shag-add': LEADER,
        'group_discount-code': group_token,
        'group_discount-validated': 'yes',
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None

    assert not payment.discounts
    group = GroupToken().deserialize(test_dao, group_token)
    # members not changed
    assert expected_members == group.members

    person = person_factory.pop()
    partner = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'full_pass-add': COUPLE,
        'rockabilly_bopper-add': COUPLE,
        'showmans_shag-add': COUPLE,
        'hurricane_shag-add': COUPLE,
        'friday_party-add': COUPLE,
        'saturday_party-add': COUPLE,
        'sunday_party-add': COUPLE,
        'group_discount-code': group_token,
        'group_discount-validated': 'yes',
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    group = GroupToken().deserialize(test_dao, group_token)
    # members not changed
    assert 3 == len(group.members)


def test_validate_discount_code_token(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                   sample_stripe_card_error, sample_stripe_successful_charge,
                                   sample_stripe_customer, mock_send_email):
    discount_code = DiscountCode(
        discount_rule='free_party_pass',
        applies_to_couple=False,
        max_usages=1,
        times_used=0,
        info='Free parties discount',
        active=True,
        included_tickets=['party_pass']
    )
    event = test_dao.get_event_by_key(mts.key)
    test_dao.add_discount_code(event, discount_code)
    token = DiscountToken().serialize(discount_code)

    res = post_json_data(client, '/check_discount_token', {
        'name': 'Mr.X',
        'location': {"city": "Cardiff", "country": "United Kingdom", "country_code": "gb"},
        'email': 'test@gmail.com',
        'discount_code-code': token,
    }).json
    assert res['success']
    assert 'Free parties discount' == res['info']
    assert ['party_pass'] == res['included_tickets']
    assert not res['name_override']
    assert not res['email_override']

    test_dao.increment_discount_code_usages(discount_code, 1)
    res = post_json_data(client, '/check_discount_token', {
        'name': 'Mr.X',
        'location': {"city": "Cardiff", "country": "United Kingdom", "country_code": "gb"},
        'email': 'test@gmail.com',
        'discount_code-code': token,
    }).json
    assert not res['success']


def test_registration_with_discount_code_party_pass(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                   sample_stripe_card_error, sample_stripe_successful_charge,
                                   sample_stripe_customer, mock_send_email):
    person = person_factory.pop()
    partner = person_factory.pop()
    discount_code = DiscountCode(
        discount_rule='free_party_pass',
        applies_to_couple=False,
        max_usages=1,
        times_used=0,
        info='Free parties discount',
        active=True,
        included_tickets=['party_pass'],
        full_name=person.full_name,
        email=person.email
    )
    event = test_dao.get_event_by_key(mts.key)
    test_dao.add_discount_code(event, discount_code)
    token = DiscountToken().serialize(discount_code)

    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'full_pass-add': COUPLE,
        'rockabilly_bopper-add': COUPLE,
        'showmans_shag-add': COUPLE,
        'hurricane_shag-add': COUPLE,
        'friday_party-add': COUPLE,
        'saturday_party-add': COUPLE,
        'sunday_party-add': COUPLE,
        'discount_code-code': token,
        'discount_code-validated': '',
    }
    assert post_json_data(client, '/check_discount_token', form_data).json['success']
    form_data['discount_code-validated'] = 'yes'

    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 55 == sum([p.value for p in payment.discounts])
    assert 120 + 120 - 55 == payment.price


def test_registration_with_discount_code_full_pass(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                                   sample_stripe_card_error, sample_stripe_successful_charge,
                                   sample_stripe_customer, mock_send_email):
    person = person_factory.pop()
    partner = person_factory.pop()
    discount_code = DiscountCode(
        discount_rule='free_full_pass',
        applies_to_couple=False,
        max_usages=1,
        times_used=0,
        info='Free full pass discount',
        active=True,
        included_tickets=['full_pass'],
        full_name=person.full_name,
        email=person.email
    )
    event = test_dao.get_event_by_key(mts.key)
    test_dao.add_discount_code(event, discount_code)
    token = DiscountToken().serialize(discount_code)

    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'dance_role': LEADER,
        'partner_name': partner.full_name,
        'partner_email': partner.email,
        'full_pass-add': COUPLE,
        'rockabilly_bopper-add': COUPLE,
        'showmans_shag-add': COUPLE,
        'hurricane_shag-add': COUPLE,
        'shag_roller_coaster-add': COUPLE,
        'friday_party-add': COUPLE,
        'saturday_party-add': COUPLE,
        'sunday_party-add': COUPLE,
        'discount_code-code': token,
        'discount_code-validated': '',
    }
    assert post_json_data(client, '/check_discount_token', form_data).json['success']
    form_data['discount_code-validated'] = 'yes'

    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 120 == sum([p.value for p in payment.discounts])
    assert 120 + 25 + 25 == payment.price


def test_update_mts_order_add_extra_station(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                          sample_stripe_card_error, sample_stripe_successful_charge,
                          sample_stripe_customer, mock_send_email):

    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'full_pass-add': LEADER,
        'rockabilly_bopper-add': LEADER,
        'showmans_shag-add': LEADER,
        'hurricane_shag-add': LEADER,
        'friday_party-add': LEADER,
        'saturday_party-add': LEADER,
        'sunday_party-add': LEADER,
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None

    reg_token = RegistrationToken().serialize(payment.paid_by)
    print(reg_token)

    form_data = {
        'registration_token': reg_token,
        'shag_roller_coaster-add': LEADER,
    }
    res = process_test_price(client, form_data, assert_disable_checkout=False)
    print(res)
    payment2 = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment2 is not None
    assert payment.paid_by == payment2.paid_by
    assert 25 == payment2.price


def test_update_mts_order_add_upgrade_to_full_pass(mts_app_routes, mts, test_dao, client, person_factory, mock_stripe,
                          sample_stripe_card_error, sample_stripe_successful_charge,
                          sample_stripe_customer, mock_send_email):

    mock_stripe.Charge.create.return_value = sample_stripe_successful_charge
    person = person_factory.pop()
    form_data = {
        'name': person.full_name,
        'email': person.email,
        'party_pass-add': LEADER,
        'hurricane_shag-add': LEADER,
        'friday_party-add': LEADER,
        'saturday_party-add': LEADER,
        'sunday_party-add': LEADER,
    }
    payment = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment is not None
    assert 85 == payment.price

    reg_token = RegistrationToken().serialize(payment.paid_by)
    print(reg_token)

    form_data = {
        'registration_token': reg_token,
        'full_pass-add': LEADER,
        'rockabilly_bopper-add': LEADER,
        'showmans_shag-add': LEADER,
    }
    res = process_test_price(client, form_data, assert_disable_checkout=False)
    payment2 = process_test_price_checkout_pay(test_dao, client, form_data)
    assert payment2 is not None
    assert payment.paid_by == payment2.paid_by
    assert 35 == payment2.price


