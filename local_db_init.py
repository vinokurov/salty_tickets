from datetime import datetime

from salty_tickets.dao import TicketsDAO
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct
from salty_tickets.config import MONGO


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

dao = TicketsDAO(host=MONGO)

event = Event(
    name='Salty Brizzle',
    key='salty_brizzle',
    start_date=SAT_MORNING_START,
    end_date=datetime(2018, 11, 18, 17, 0),
    info='Salty Brizzle Weekender',
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
        start_datetime=SAT_NOON_START,
        end_datetime=SAT_NOON_END,
        teachers=MICHAL_KASIA,
        level='intermed./adv.',
        **kwargs,
    ),
    WorkshopProduct(
        name=MICHAL_KASIA + ' - Adv 2',
        key='mk_adv_2',
        info='2nd adv class by ' + MICHAL_KASIA,
        start_datetime=SUN_NOON_START,
        end_datetime=SUN_NOON_END,
        teachers=MICHAL_KASIA,
        level='intermed./adv.',
        **kwargs,
    ),
    WorkshopProduct(
        name=NIAL_ANNABELLE + ' - Adv 1',
        key='na_adv_1',
        info='Rhythm breaks - description TBC.',
        start_datetime=SAT_MORNING_START,
        end_datetime=SAT_MORNING_END,
        teachers=NIAL_ANNABELLE,
        level='intermed./adv.',
        **kwargs,
    ),
    WorkshopProduct(
        name=NIAL_ANNABELLE + ' - Adv 2',
        key='na_adv_2',
        info='Democracy Sausage (Styling and footwork): Dancing shag is a team effort, we\'ll show you ways that you can both express your own styling as well as working with your partner\'s styling.',
        start_datetime=SUN_MORNING_START,
        end_datetime=SUN_MORNING_END,
        teachers=NIAL_ANNABELLE,
        level='intermed./adv.',
        **kwargs,
    ),

    WorkshopProduct(
        name=MICHAL_KASIA + ' - Int 1',
        key='mk_int_1',
        info='1st int class by ' + MICHAL_KASIA,
        start_datetime=SAT_MORNING_START,
        end_datetime=SAT_MORNING_END,
        teachers=MICHAL_KASIA,
        level='improv./intermed.',
        **kwargs,
    ),
    WorkshopProduct(
        name=MICHAL_KASIA + ' - Int 2',
        key='mk_int_2',
        info='2nd int class by ' + MICHAL_KASIA,
        start_datetime=SUN_MORNING_START,
        end_datetime=SUN_MORNING_END,
        teachers=MICHAL_KASIA,
        level='improv./intermed.',
        **kwargs,
    ),
    WorkshopProduct(
        name=NIAL_ANNABELLE + ' - Int 1',
        key='na_int_1',
        info='Emu Egg Scramble (Turns and flow): We\'ll be working through some fun turns involving flow and momentum, try not to get too scrambled!',
        start_datetime=SAT_NOON_START,
        end_datetime=SAT_NOON_END,
        teachers=NIAL_ANNABELLE,
        level='improv./intermed.',
        **kwargs,
    ),
    WorkshopProduct(
        name=NIAL_ANNABELLE + ' - Int 2',
        key='na_int_2',
        info='Kangaroo on a Spit (Circular moves and rotation): Rotation, rotation, rotation. We love using rotation in our shag and changing between different rotating shapes, we hope you\'ll love it too.',
        start_datetime=SUN_NOON_START,
        end_datetime=SUN_NOON_END,
        teachers=NIAL_ANNABELLE,
        level='improv./intermed.',
        **kwargs,
    ),
]

event.append_products(products)

event.layout = dict(
    workshops=dict(
        Saturday=[
            {r'Improv/Intermed':'mk_int_1', r'Intermed/Adv': 'na_adv_1'},
            {r'Improv/Intermed':'na_int_1', r'Intermed/Adv': 'mk_adv_1'},
        ],
        Sunday=[
            {r'Improv/Intermed':'mk_int_2', r'Intermed/Adv': 'na_adv_2'},
            {r'Improv/Intermed':'na_int_2', r'Intermed/Adv': 'mk_adv_2'},
        ],
    )
)

dao.create_event(event)
print(event)
print(event.id)
