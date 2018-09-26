from datetime import datetime

from salty_tickets.dao import TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct


SAT_MORNING_START = datetime(2018, 11, 17, 11, 0)
SAT_MORNING_END = datetime(2018, 11, 17, 13, 15)

SAT_NOON_START = datetime(2018, 11, 17, 14, 15)
SAT_NOON_END = datetime(2018, 11, 17, 16, 30)

SUN_MORNING_START = datetime(2018, 11, 18, 10, 30)
SUN_MORNING_END = datetime(2018, 11, 18, 12, 45)

SUN_NOON_START = datetime(2018, 11, 18, 13, 30)
SUN_NOON_END = datetime(2018, 11, 18, 15, 45)


NIAL_ANNABELLE = 'Nial & Annabelle'
MICHAL_KASIA = "Michal & Kasia"

dao = TicketsDAO(host=r'mongodb://localhost:27017/salty_tickets')

event = Event(
    name='Salty Breezle',
    key='salty_breezle',
    start_date=SAT_MORNING_START,
    end_date=datetime(2018, 11, 18, 17, 0),
    info='Salty Breezle Weekender',
    pricing_rules=[
        {
            "name": "combination",
            "kwargs": {
                "tag": "workshop",
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
            "name": "at_least_any_with_tag",
            "kwargs": {
                "tag": "workshop",
                "count": 2,
                "error_text": "Please select at least 2 workshops per person."
            }
        },
        {
            "name": "non_overlapping",
            "kwargs": {
                "tag": "workshop",
                "error_text": "Workshops shouldn't overlap in time."
            }
        }
    ],
)

kwargs = dict(
    ratio=1.4,
    allow_first=5,
    max_available=30,
    base_price=27.5,
    tags={'workshop'}
)

products = [
    WorkshopProduct(
        name=MICHAL_KASIA + ' - Adv 1',
        key='mk_adv_1',
        info='1st adv class by ' + MICHAL_KASIA,
        start_datetime=SAT_MORNING_START,
        end_datetime=SAT_MORNING_END,
        teachers=MICHAL_KASIA,
        level='advanced',
        **kwargs,
    ),
    WorkshopProduct(
        name=MICHAL_KASIA + ' - Adv 2',
        key='mk_adv_2',
        info='2nd adv class by ' + MICHAL_KASIA,
        start_datetime=SUN_NOON_START,
        end_datetime=SUN_NOON_END,
        teachers=MICHAL_KASIA,
        level='advanced',
        **kwargs,
    ),
    WorkshopProduct(
        name=NIAL_ANNABELLE + ' - Adv 1',
        key='na_adv_1',
        info='1st adv class by ' + NIAL_ANNABELLE,
        start_datetime=SAT_NOON_START,
        end_datetime=SAT_NOON_END,
        teachers=NIAL_ANNABELLE,
        level='advanced',
        **kwargs,
    ),
    WorkshopProduct(
        name=NIAL_ANNABELLE + ' - Adv 2',
        key='na_adv_2',
        info='2nd adv class by ' + NIAL_ANNABELLE,
        start_datetime=SUN_MORNING_START,
        end_datetime=SUN_MORNING_END,
        teachers=NIAL_ANNABELLE,
        level='advanced',
        **kwargs,
    ),

    WorkshopProduct(
        name=MICHAL_KASIA + ' - Int 1',
        key='mk_int_1',
        info='1st int class by ' + MICHAL_KASIA,
        start_datetime=SAT_NOON_START,
        end_datetime=SAT_NOON_END,
        teachers=MICHAL_KASIA,
        level='intermediate',
        **kwargs,
    ),
    WorkshopProduct(
        name=MICHAL_KASIA + ' - Int 2',
        key='mk_int_2',
        info='2nd int class by ' + MICHAL_KASIA,
        start_datetime=SUN_MORNING_START,
        end_datetime=SUN_MORNING_END,
        teachers=MICHAL_KASIA,
        level='intermediate',
        **kwargs,
    ),
    WorkshopProduct(
        name=NIAL_ANNABELLE + ' - Int 1',
        key='na_int_1',
        info='1st int class by ' + NIAL_ANNABELLE,
        start_datetime=SAT_MORNING_START,
        end_datetime=SAT_MORNING_END,
        teachers=NIAL_ANNABELLE,
        level='intermediate',
        **kwargs,
    ),
    WorkshopProduct(
        name=NIAL_ANNABELLE + ' - Int 2',
        key='na_int_2',
        info='2nd int class by ' + NIAL_ANNABELLE,
        start_datetime=SUN_NOON_START,
        end_datetime=SUN_NOON_END,
        teachers=NIAL_ANNABELLE,
        level='intermediate',
        **kwargs,
    ),
]

event.append_products(products)

event.layout = dict(
    workshops=dict(
        Saturday=[
            dict(Intermediate='na_int_1', Advanced='mk_adv_1'),
            dict(Intermediate='mk_int_1', Advanced='na_adv_1'),
        ],
        Sunday=[
            dict(Intermediate='mk_int_2', Advanced='na_adv_2'),
            dict(Intermediate='na_int_2', Advanced='mk_adv_2'),
        ],
    )
)

dao.create_event(event)
print(event)
print(event.id)
