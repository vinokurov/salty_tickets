from datetime import datetime

from salty_tickets.dao import TicketsDAO
from salty_tickets.models.discounts import GroupDiscountProduct, FixedValueDiscountProduct, CodeDiscountProduct
from salty_tickets.models.event import Event
from salty_tickets.models.products import Product
from salty_tickets.models.tickets import WorkshopTicket, PartyTicket, FestivalPassTicket
from salty_tickets.config import MONGO


TIME_SAT_0 = {'start_datetime': datetime(2019, 3, 30, 10, 0),
              'end_datetime': datetime(2019, 3, 30, 11, 0)}

TIME_SAT_1 = {'start_datetime': datetime(2019, 3, 30, 11, 0),
              'end_datetime': datetime(2019, 3, 30, 13, 0)}

TIME_SAT_1a = {'start_datetime': datetime(2019, 3, 30, 13, 0),
               'end_datetime': datetime(2019, 3, 30, 14, 0)}

TIME_SAT_2 = {'start_datetime': datetime(2019, 3, 30, 14, 0),
              'end_datetime': datetime(2019, 3, 30, 16, 0)}

TIME_SAT_3 = {'start_datetime': datetime(2019, 3, 30, 16, 30),
              'end_datetime': datetime(2019, 3, 30, 18, 30)}

TIME_SUN_1 = {'start_datetime': datetime(2019, 3, 31, 11, 0),
              'end_datetime': datetime(2019, 3, 31, 13, 0)}

TIME_SUN_2 = {'start_datetime': datetime(2019, 3, 31, 14, 0),
              'end_datetime': datetime(2019, 3, 31, 16, 0)}

TIME_SUN_3 = {'start_datetime': datetime(2019, 3, 31, 16, 30),
              'end_datetime': datetime(2019, 3, 31, 18, 30)}

TEACH_PA = 'Fancy & Patrick'
TEACH_PF = 'Aila & Peter'
TEACH_FC = 'Cherry & Filip'
TEACH_RS = 'Simona & Rokas'
TEACH_TM = 'Maja & Teis'
TEACH_HL = 'Larissa & Heiko'

LEV_SLS = 'St.Louis Shag'
LEV_CSH = 'Collegiate Shag'
LEV_VET = 'Collegiate Shag Veteran'
LEV_NOV = 'Collegiate Shag Novice'

dao = TicketsDAO(host=MONGO)

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
        info="Learn how to dance to Rockabilly Bopper music and learn a short choreography focusing on RnB musicality.",
        teachers=TEACH_PF,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SUN_1,
    ),
    WorkshopTicket(
        name='Creme de la Creme Shag',
        info="Top-level moves that don't get taught in class. These secrets require courage and strong nerves, the question is are you ready?",
        teachers=TEACH_PF,
        level=LEV_VET,
        **kwargs_station,
        **TIME_SAT_2,
    ),
    WorkshopTicket(
        name="Showman's Shag",
        key='showmans_shag',
        info='What it takes to throw down a real game in the dancefloor and boost your competition & perfromance skills. ',
        teachers=TEACH_PF,
        level=LEV_VET,
        **kwargs_station,
        **TIME_SAT_1,
    ),
    WorkshopTicket(
        name='St.Louis Cocktail',
        info='This station will introduce you to the mixology of the favourite St.Louis Shag ingridients from Rokas & Simona. Learn them, try them and make your own cocktail.',
        teachers=TEACH_RS,
        level=LEV_SLS,
        **kwargs_station,
        **TIME_SUN_1,
    ),
    WorkshopTicket(
        name='St.Louis Orbits',
        info='Get ready to travel the orbits and blow your mind with unseen St.Louis Shag swing out variations.',
        teachers=TEACH_RS,
        level=LEV_SLS,
        **kwargs_station,
        **TIME_SAT_3,
    ),
    WorkshopTicket(
        name='St.Louis from A to Z',
        key='st_louis_a_z',
        info='You are an experienced swing dancer, but want to try new styles. In these 2h Rokas & Simona, the best St.Louis Shaggers in Europe, will challenge you to learn the fundamentals of the footwork and connection as well as the must have repertoire for social dancing.',
        teachers=TEACH_RS,
        level=LEV_SLS,
        **kwargs_station,
        **TIME_SAT_2,
    ),
    WorkshopTicket(
        name='Hurracaine Shag',
        info='Focusing on dancing big and wild with a lot of energy; whole body movement, efficient connection and exchanging energy between partners.',
        teachers=TEACH_FC,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SAT_1,
    ),
    WorkshopTicket(
        name='Shag Roller Coaster',
        info='Do you want more adrenaline? Be prepared for the breathtaking ride through dynamic ups and downs, rhythmical accents, unexpected breaks and footworks from the champions of Camp Hollywood 2018.',
        teachers=TEACH_FC,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SUN_2,
    ),
    WorkshopTicket(
        name='Fast & Furious Shag',
        info='The worldwide champions of endurance competitions (1st place at BCN 2017/18 & LA 2018) will show you their fast feet technique to  make your shag more efficient, fun, relaxed at a speed above 300 bpm.',
        teachers=TEACH_TM,
        level=LEV_VET,
        **kwargs_station,
        **TIME_SUN_1,
    ),
    WorkshopTicket(
        name='Shag Boomerang',
        info='Shag out and get sugar pushed back.This station is for everyone who wants to add sugar and exploding excitement to the way you do shag outs! We’ll be playing with the idea of reversing the shag outs, so be ready to surprise your surroundings and to overcome the calculated pattern of what might be your ‘normal’ shag out. And let’s fine-tune your sugar pushes and let’s use them both intuitively and as a natural part of shaping those sharp shag-outs!',
        teachers=TEACH_TM,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SUN_3,
    ),
    WorkshopTicket(
        name='Atomic Shag',
        info='Master the quantum mechanics of controling your flow and releasing your energy. We will explore smooth sequences and contrast them with some of our favorite power moves like slides, drops and turns. ',
        teachers=TEACH_HL,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SAT_3,
    ),
    WorkshopTicket(
        name="Millionaire's Shag",
        key="millionaire_shag",
        info='Millionaire Shagsters invest their energy wisely and look sharp the whole night. They know how to add some Balboa and elegancy to Shag and how to use momentum to get rich dances. Join if you wanna get rich too!',
        teachers=TEACH_HL,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SUN_3,
    ),
    WorkshopTicket(
        name='Shag Hall of Fame',
        info='Travel coast to coast from Venice Beach to Mister Ghost! In this session we’ll dig deeper into the history of Shag with classic styling, moves, and sequences from old school Shag clips danced by the greats including Ray Hirsch & Patti Lacey, Connie Weidell & Marion Goldie, and William Ledger & Virginia Hart. There’s a lot to be learnt from the old school dancers, so prepare to be challenged!',
        teachers=TEACH_PA,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SUN_2,
    ),
    WorkshopTicket(
        name='Shag Carousel',
        info='"Dance in circles big and small in this revolutionary class! Together we’ll work on a varied mixture of spins, circles, orbits, rotations and ruedas, carefully curated to minimise dizziness and maximise merriment!"',
        teachers=TEACH_PA,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SAT_2,
    ),
    WorkshopTicket(
        name='Shag ABC',
        info='You\'ve been swing dancer for a while, but you want to get in on the shag fun? This station is for you. We will start with the ABC of shag (basics and connection), but will move on quickly to get you shagging in no time.',
        teachers=TEACH_FC,
        level=LEV_NOV,
        **kwargs_train,
        **TIME_SAT_0,
    ),
    WorkshopTicket(
        name='Shag Essentials',
        info='Complete your shag degree by learning the must have social moves and transitions with the 2 international star teacher couples. ',
        teachers=f'{TEACH_HL}, {TEACH_TM}',
        level=LEV_NOV,
        **kwargs_train,
        **TIME_SAT_1,
    ),
    WorkshopTicket(
        name='Shag Clinic',
        info='This station is ideal if you want to work instensively and focus on refining your shag. Two top level international teacher couples (1hr each) will work with you in a small group (up to 6 couples) on the material that you choose, and give you personal feedback.',
        teachers=f'{TEACH_PA}, {TEACH_PF}',
        level=LEV_VET,
        ratio=1.0,
        allow_first=0,
        max_available=12,
        base_price=40.0,
        tags={'mts', 'station', 'clinic'},
        **TIME_SAT_3,
    ),
    PartyTicket(
        name='Friday Party',
        info='Friday Party',
        start_datetime=datetime(2019, 3, 29, 20, 0),
        end_datetime=datetime(2019, 3, 30, 2, 0),
        location='Limehouse Townhall',
        base_price=25.0,
        max_available=200,
        tags={'party'},
    ),
    PartyTicket(
        name='Saturday Party',
        info='Saturday Party',
        start_datetime=datetime(2019, 3, 30, 20, 0),
        end_datetime=datetime(2019, 3, 31, 2, 0),
        location='Limehouse Townhall',
        base_price=25.0,
        max_available=200,
        tags={'party'},
    ),
    PartyTicket(
        name='Sunday Party',
        info='Sunday Party ',
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
            'red': 'Red',
        }
    ),
    Product(
        name='T-shirt',
        key='tshirt',
        tags={'merchandise'},
        base_price=20.0,
        image_urls=[
            {'url': 'https://de9luwq5d40h2.cloudfront.net/catalog/product/large_image/05_407044.jpg', 'text': 'Front'},
            {'url': 'https://de9luwq5d40h2.cloudfront.net/catalog/product/large_image/407044_sub2.jpg', 'text': 'Back'}
        ],
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

event.layout = dict(
    workshops=dict(
        Saturday=[
            {'1': 'shag_abc',           '2': '',                '3': ''},
            {'1': 'shag_essentials',    '2': 'hurracaine_shag', '3': 'showmans_shag'},
            {'1': 'st_louis_a_z',       '2': 'shag_carousel',   '3': 'creme_de_la_creme_shag'},
            {'1': 'st_louis_orbits',    '2': 'atomic_shag',     '3': 'shag_clinic'},
        ],
        Sunday=[
            {'1': 'rockabilly_bopper_shag', '2': 'fast_furious_shag',     '3': 'st_louis_cocktail'},
            {'1': 'shag_roller_coaster',    '2': 'shag_hall_of_fame',     '3': ''},
            {'1': 'millionaire_shag',       '2': 'shag_boomerang',        '3': ''},
        ],
    )
)

dao.create_event(event)
print(event.id)
