from datetime import datetime

from salty_tickets.dao import TicketsDAO
from salty_tickets.models.discounts import GroupDiscountProduct, FixedValueDiscountProduct, CodeDiscountProduct
from salty_tickets.models.event import Event
from salty_tickets.models.products import Product
from salty_tickets.models.tickets import WorkshopTicket, PartyTicket, FestivalPassTicket
from salty_tickets.config import MONGO
from salty_tickets.tasks import update_event_numbers

TIME_FRI_0 = {'start_datetime': datetime(2020, 3, 20, 19, 30),
              'end_datetime': datetime(2020, 3, 20, 21, 0)}

TIME_SAT_1 = {'start_datetime': datetime(2020, 3, 21, 11, 0),
              'end_datetime': datetime(2020, 3, 21, 13, 0)}

TIME_SAT_2 = {'start_datetime': datetime(2020, 3, 21, 13, 30),
              'end_datetime': datetime(2020, 3, 21, 15, 30)}

TIME_SUN_1 = {'start_datetime': datetime(2020, 3, 22, 10, 30),
              'end_datetime': datetime(2020, 3, 22, 12, 30)}

TIME_SUN_2 = {'start_datetime': datetime(2020, 3, 22, 12, 45),
              'end_datetime': datetime(2020, 3, 22, 14, 45)}

TIME_SUN_3 = {'start_datetime': datetime(2020, 3, 22, 15, 0),
              'end_datetime': datetime(2020, 3, 2, 17, 0)}

TEACH_MM = 'Moe & Mike'
TEACH_SK = 'Shawn & Krystal'
TEACH_SP = 'Sara & Pol'
TEACH_AP = 'Aila & Peter'
TEACH_KA = 'Krystal & Alex'

LEV_GEN = 'Collegiate Shag General'
LEV_ADV = 'Collegiate Shag Advanced'
LEV_BEG = 'Collegiate Shag Beginner'

LOC_LIME = 'Limehouse Townhall'
LOC_HAGG = 'Haggerston Centre Studio'
LOC_C151 = 'Centre 151 Studio'
LOC_GRAE = 'Graeae Theatre Studio'

dao = TicketsDAO(host=MONGO)

event = Event(
    name='Mind the Shag 2020',
    key='mind_the_shag_2020',
    start_date=datetime(2020, 3, 20, 19, 0),
    end_date=datetime(2020, 3, 22, 23, 0),
    info='Mind the Shag - London Shag Festival',
    active=True,
    pricing_rules=[
        {
            "name": "mind_the_shag",
            "kwargs": {
                "price_station": 30.0,
                "price_clinic": 35.0,
                "price_station_extra": 25.0,
                'price_cheaper_station_extra': 19.0
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
        },
        {
            'name': 'at_least_any_with_tag',
            'kwargs': {
                'tag': 'includes_parties',
                'error_text': 'Super-Offpeak registration needs to have a Full Pass or Beginners Track with parties.'
            }
        },
        {
            'name': 'mind_the_shag',
            'kwargs': {
                'tag': 'mts', # not used
            },
        },
    ],
)

kwargs_station = dict(
    ratio=1.5,
    allow_first=5,
    max_available=40,
    base_price=30.0,
    tags={'station'}
)

kwargs_train = dict(
    ratio=1.5,
    allow_first=5,
    max_available=40,
    base_price=30.0,
    tags={'station', 'train'}
)

tickets = [
    WorkshopTicket(
        name='Shag Roots',
        info="Beginner shag. "
             "You've been a swing dancer for a while, but you want to get in on the Shag fun? "
             "This station is for you! We will start with the ABC of Shag (basics and connection), "
             "but will move on quickly to get you shagging in no time.",
        teachers=TEACH_KA,
        level=LEV_BEG,
        location=LOC_LIME,
        **kwargs_train,
        **TIME_FRI_0,
    ),
    WorkshopTicket(
        name='Rising Shag',
        info="Essential Shag vocabulary. "
             "Learn the must-have Collegiate Shag social moves and transitions. "
             "The station is the second part of the Shag Beginner track, but can also be interesting on its own "
             "for those who want to consolidate their Shag repertoire.",
        teachers=TEACH_KA,
        level=LEV_BEG,
        location=LOC_GRAE,
        **kwargs_train,
        **TIME_SAT_1,
    ),
    WorkshopTicket(
        name='Shag to Impress',
        info="Competition skills. "
             "If you want to compete with the best then you need not only to dance well but to look good, too! "
             "Looking good isn’t only what you wear, but how you wear it, "
             "it’s not just what you move, but how you move it. "
             "We’ll show you how to win over the judges and the audience, "
             "so when you walk onto the floor all eyes are on you, "
             "like James Bond walking into a casino. "
             "Mike & Moe are true experts of competitions, as they have been competing and "
             "judging at the top international Shag and other swing-dance style contests.",
        teachers=TEACH_MM,
        level=LEV_GEN,
        location=LOC_HAGG,
        **kwargs_station,
        **TIME_SAT_1,
    ),
    WorkshopTicket(
        name="Aero Shag",
        info="Mini aerials, jumps and dips. "
             "Learn some easy mini aerials and tricks and how to integrate them "
             "into your Shag dancing from the masters.",
        teachers=TEACH_SP,
        level=LEV_ADV,
        location=LOC_GRAE,
        **kwargs_station,
        **TIME_SAT_2,
    ),
    WorkshopTicket(
        name='Killer Feet',
        info="Perfecting footwork. ",
        teachers=TEACH_SK,
        level=LEV_GEN,
        location=LOC_HAGG,
        **kwargs_station,
        **TIME_SAT_2,
    ),
    WorkshopTicket(
        name='Shag Anatomy',
        info="Styling using all parts of the body. "
             "Anatomy is the study of the structure of an object, "
             "in this case the parts of your body that are used while dancing Shag! "
             "Aila & Peter will go through the different parts of the body and "
             "guide you in how to use them to make better/different shapes, have better connection, "
             "and dance from the tips of the fingers to the tips of the toes.",
        teachers=TEACH_AP,
        level=LEV_ADV,
        location=LOC_C151,
        **kwargs_station,
        **TIME_SUN_1,
    ),
    WorkshopTicket(
        name='Kicks Club',
        info="Moves with kicks. "
             "Do you want to make your Shag look and feel wild, big and expressive? "
             "Kicks is the right way to go. "
             "In this station Pol & Sara will explore the world of kick moves such as "
             "Collegiate Kicks, Cross Kicks, Hesitation Kicks and their variations.",
        teachers=TEACH_SP,
        level=LEV_GEN,
        location=LOC_HAGG,
        **kwargs_station,
        **TIME_SUN_1,
    ),
    WorkshopTicket(
        name='All that Shag',
        info="Musicality with live music. "
             "Make your dancing musicality pop. "
             "Learn how to complement music by mixing contrasting small and large moves, "
             "adding footwork variations and jazz steps, and hitting those rhythms and breaks. "
             "This station will have live music accompaniment.",
        teachers=TEACH_SP,
        level=LEV_ADV,
        location=LOC_C151,
        **kwargs_station,
        **TIME_SUN_2,
    ),
    WorkshopTicket(
        name='Smooth as Butter',
        info="Smooth shag. "
             "Even if you like your shag wild and crazy, there's always room to smooth it out. "
             "Variety adds dynamics to your dancing, keeping it fresh. "
             "A swing song has a variety of energy levels in it, and so should your dancing. "
             "We'll be talking connection - to your partner, to the floor, and of course to the music. "
             "We'll show you some smooth moves using these techniques to help you glide "
             "across the floor like butter on an English muffin!",
        teachers=TEACH_MM,
        level=LEV_GEN,
        location=LOC_HAGG,
        **kwargs_station,
        **TIME_SUN_2,
    ),
    WorkshopTicket(
        name='Old Skool Shag',
        info="Classic moves. "
             "Moe and Mike have been doing this a long time, oh the things they’ve seen! "
             "Time to bring back some of those classic moves from days gone by and "
             "give them a fresh coat of paint. Some that they’ve done and some from the golden age of VHS!",
        teachers=TEACH_MM,
        level=LEV_GEN,
        location=LOC_C151,
        **kwargs_station,
        **TIME_SUN_3,
    ),
    WorkshopTicket(
        name='Shag Traveller',
        info="Travelling moves. "
             "Aila & Peter will provide you with travelling moves to explore every inch of the dance floor. "
             "These moves will help your Shag become more dynamic, fast and smooth by travelling and "
             "changing direction. Learn promenade variations, side-by-side positions, different footwork, "
             "and moves such as spins while travelling.",
        teachers=TEACH_AP,
        level=LEV_GEN,
        location=LOC_HAGG,
        **kwargs_station,
        **TIME_SUN_3,
    ),
    ############
    # WorkshopTicket(
    #     name='Shag Clinic',
    #     info='This station is ideal if you want to work instensively and focus on refining your shag. Two top level international teacher couples (1hr each) will work with you in a small group (up to 6 couples) on the material that you choose, and give you personal feedback.',
    #     teachers=f'{TEACH_PA}, {TEACH_PF}',
    #     level=LEV_ADV,
    #     ratio=1.0,
    #     allow_first=0,
    #     max_available=12,
    #     base_price=40.0,
    #     tags={'mts', 'station', 'clinic'},
    #     **TIME_SAT_3,
    # ),
    #########################
    PartyTicket(
        name='Boat Trip 1',
        info='Regents canal boat trip with live band. From Paddington to Kings Cross. '
             'Departs at 14:00 from Paddington. Arrives at 16:30 at Kings Cross.',
        start_datetime=datetime(2020, 3, 21, 13, 0),
        end_datetime=datetime(2020, 3, 21, 17, 0),
        location='Paddington to Kings Cross',
        base_price=35.0,
        max_available=50,
        tags={'mts', 'station', 'clinic', 'extra'},
    ),
    PartyTicket(
        name='Boat Trip 2',
        info='Regents canal boat trip with live band. From Kings Cross to Paddington. '
             'Departs at 16:30 from Kings Cross. Arrives at 19:00 at Paddington.',
        start_datetime=datetime(2020, 3, 21, 16, 0),
        end_datetime=datetime(2020, 3, 21, 20, 0),
        location='Kings Cross to Paddington',
        base_price=35.0,
        max_available=50,
        tags={'mts', 'station', 'clinic', 'extra'},
    ),
    PartyTicket(
        name='Sunday Roast',
        info='Traditional British Sunday meal in a traditional London pub. '
             'The deal includes any sunday roast (beef, chicken, pork, or veggie) or fish & chips, '
             'and a pint of local brewed beer.  (vegan? Just ask for no yorkie!)',
        start_datetime=datetime(2020, 3, 22, 18, 0),
        end_datetime=datetime(2020, 3, 22, 20, 0),
        location='Hoxton Brewhouse Pub',
        base_price=19.0,
        max_available=50,
        tags={'mts', 'station', 'cheaper_station', 'extra'},
    ),
    #########################
    PartyTicket(
        name='Friday Party',
        info='Friday Party',
        start_datetime=datetime(2020, 3, 20, 21, 0),
        end_datetime=datetime(2020, 3, 21, 2, 0),
        location=LOC_LIME,
        base_price=25.0,
        max_available=200,
        tags={'party'},
    ),
    PartyTicket(
        name='Saturday Party',
        info='Saturday Party',
        start_datetime=datetime(2020, 3, 21, 20, 0),
        end_datetime=datetime(2020, 3, 22, 2, 0),
        location=LOC_LIME,
        base_price=30.0,
        max_available=200,
        tags={'party'},
    ),
    PartyTicket(
        name='Sunday Party',
        info='Sunday Party ',
        start_datetime=datetime(2020, 3, 22, 20, 0),
        end_datetime=datetime(2020, 3, 23, 1, 0),
        location='Jago Bar',
        base_price=20.0,
        max_available=150,
        tags={'party'},
    ),
    FestivalPassTicket(
        name='Full Pass',
        key='full_pass',
        info='Includes 3 stations and all parties',
        base_price=150.0,
        tags={'pass', 'includes_parties', 'station_discount_3', 'group_discount', 'overseas_discount'},
    ),
    FestivalPassTicket(
        name='Beginner Track',
        key='shag_novice',
        info='Intensive beginner shag training and all parties',
        base_price=110.0,
        tags={'pass', 'includes_parties', 'station_discount_2', 'group_discount', 'overseas_discount'},
    ),
    FestivalPassTicket(
        name='Shag Novice Track w/o parties',
        key='shag_novice_no_parties',
        info='Intensive beginner shag and no parties',
        base_price=55.0,
        tags={'pass', 'station_discount_2'},
    ),
    FestivalPassTicket(
        name='Party Pass',
        key='party_pass',
        info='Includes all 3 parties',
        base_price=65.0,
        tags={'pass', 'includes_parties'},
    ),
]

products = [
    # Product(
    #     name='Tote bag',
    #     key='tote_bag',
    #     tags={'merchandise'},
    #     base_price=5.0,
    #     options={
    #         'blue': 'Navy Blue',
    #         'red': 'Red',
    #     }
    # ),
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
    # Product(
    #     name='Bottle',
    #     key='bottle',
    #     tags={'merchandise'},
    #     base_price=5.0,
    #     options={
    #         'blue': 'Navy Blue',
    #     }
    # ),
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
        discount_value=10,
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
        Friday=[
            {'1': 'shag_roots'},
        ],
        Saturday=[
            {'1': 'rising_shag',        '2': 'shag_to_impress', '3': ''},
            {'1': 'aero_shag',          '2': 'killer_feet',     '3': 'boat_trip_1'},
            {'1': '',                   '2':              '',   '3': 'boat_trip_2'},
        ],
        Sunday=[
            {'1': 'shag_anatomy',           '2': 'kicks_club',},
            {'1': 'all_that_shag',          '2': 'smooth_as_butter',},
            {'1': 'old_skool_shag',         '2': 'shag_traveller',},
            {'1': 'sunday_roast',           '2': '',},
        ],
    )
)

dao.create_event(event)
event = dao.get_event_by_key(event.key)
update_event_numbers(dao, event)
print(event.id)
