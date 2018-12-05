from datetime import datetime

import pytest
from salty_tickets.api.registration_process import do_price, do_checkout, do_pay, do_get_payment_status, \
    do_check_partner_token
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct, PartyProduct, FestivalPass
from salty_tickets.models.merchandise import MerchandiseProduct
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
                "name": "combination",
                "kwargs": {
                    "tag": "station",
                    "count_prices": {
                        "2": 55.0,
                        "3": 75.0,
                        "4": 90.0,
                    }
                }
            }
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
        tags={'mts','station'}
    )

    kwargs_train = dict(
        ratio=1.5,
        allow_first=5,
        max_available=30,
        base_price=27.5,
        tags={'mts', 'station', 'fast_train'}
    )

    products = [
        WorkshopProduct(
            name='Rockabilly Bopper Shag',
            key='rockabilly_bopper',
            info='Rockabilly Bopper Shag info',
            start_datetime=datetime(2019, 3, 30, 11, 0),
            end_datetime=datetime(2019, 3, 30, 13, 0),
            teachers='Patrick & Fancy',
            level='collegiate any',
            **kwargs_station,
        ),
        WorkshopProduct(
            name='St.Louis Cocktail',
            key='stl_cocktail',
            info='St.Louis Cocktail info',
            start_datetime=datetime(2019, 3, 30, 11, 0),
            end_datetime=datetime(2019, 3, 30, 13, 0),
            teachers='Rokas & Simona',
            level='St.Louis Any',
            **kwargs_station,
        ),
        WorkshopProduct(
            name='Showmans Shag',
            key='showmans_shag',
            info='Showmans Shag info',
            start_datetime=datetime(2019, 3, 30, 14, 0),
            end_datetime=datetime(2019, 3, 30, 16, 0),
            teachers='Partick & Fancy',
            level='Collegiate Adv',
            **kwargs_station,
        ),
        WorkshopProduct(
            name='Savoy Shag',
            key='savoy_shag',
            info='Savoy Shag info',
            start_datetime=datetime(2019, 3, 30, 14, 0),
            end_datetime=datetime(2019, 3, 30, 16, 0),
            teachers='Teis & Maja',
            level='Collegiate Any',
            **kwargs_station,
        ),
        WorkshopProduct(
            name='Hurricane Shag',
            key='hurricane_shag',
            info='Hurricane Shag info',
            start_datetime=datetime(2019, 3, 30, 16, 30),
            end_datetime=datetime(2019, 3, 30, 18, 30),
            teachers='Filip & Cherry',
            level='Collegiate Any',
            **kwargs_station,
        ),
        WorkshopProduct(
            name='Shag Roots',
            key='shag_roots',
            info='Shag Roots info',
            start_datetime=datetime(2019, 3, 30, 11, 0),
            end_datetime=datetime(2019, 3, 30, 13, 0),
            teachers='Filip & Cherry',
            level='Collegiate Beginner',
            **kwargs_train,
        ),
        WorkshopProduct(
            name='Rising Shag',
            key='rising_shag',
            info='Rising Shag info',
            start_datetime=datetime(2019, 3, 30, 14, 0),
            end_datetime=datetime(2019, 3, 30, 16, 0),
            teachers='Filip & Cherry',
            level='Collegiate Beginner',
            **kwargs_train,
        ),
        WorkshopProduct(
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
        PartyProduct(
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
        PartyProduct(
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
        PartyProduct(
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
        FestivalPass(
            name='Full Weekend Ticket',
            key='full_weekend_ticket',
            info='Includes 3 stations and all parties',
            base_price=120.0,
            includes={
                'party': 3,
                'station': 3,
            },
        ),
        FestivalPass(
            name='Full Weekend Ticket w/o parties',
            key='full_weekend_ticket_no_parties',
            info='Includes 3 stations and no parties',
            base_price=75.0,
            includes={
                'station': 3,
            },
        ),
        FestivalPass(
            name='Fast Shag Train',
            key='fast_shag_train',
            info='Intensive beginner shag training and all parties',
            base_price=90.0,
            includes={
                'party': 3,
                'train': 2,
            },
        ),
        FestivalPass(
            name='Fast Shag Train w/o parties',
            key='fast_shag_train_no_parties',
            info='Intensive beginner shag and no parties',
            base_price=45.0,
            includes={
                'train': 2,
            },
        ),
        FestivalPass(
            name='Party Pass',
            key='party_pass',
            info='Includes all 3 parties',
            base_price=55.0,
            includes={
                'party': 3,
            },
        ),
        MerchandiseProduct(
            name='Tote bag',
            key='tote_bag',
            tags={'merchandise'},
            base_price=5.0,
            options={
                'blue': 'Navy Blue',
                'red': 'Burgundy Red',
            }
        ),
        MerchandiseProduct(
            name='T-shirt',
            key='tshirt',
            tags={'merchandise'},
            base_price=15.0,
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
        MerchandiseProduct(
            name='Bottle',
            key='bottle',
            tags={'merchandise'},
            base_price=4.0,
            options={
                'blue': 'Navy Blue',
            }
        ),
    ]

    event.append_products(products)
    test_dao.create_event(event)


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

    @app.route('/user_order', methods=['GET'])
    def user_order_index():
        pass