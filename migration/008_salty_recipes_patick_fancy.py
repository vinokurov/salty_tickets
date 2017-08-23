import json
import datetime

from salty_tickets import database
from salty_tickets import models
from salty_tickets import products

event = models.Event.query.filter_by(event_key='salty_recipes_with_pol_sara').one()
event.active = False
database.db_session.commit()

event = models.Event.query.filter_by(event_key='salty_jitterbugs_contest_10_07').one()
event.active = False
database.db_session.commit()


event = models.Event(
    name='Salty Recipes with Patrick & Fancy',
    start_date=datetime.datetime(2017, 9, 17),
    event_type='dance'
)

database.db_session.add(event)

salty_persons = [
    "Alison porter",
    "Aman Hothi",
    "Amelie Rousseau",
    "Anitha Baliga",
    "Anthony Carr",
    "Carla Sanchez Martinez",
    "Cathy Kennedy",
    "Despoina Magka",
    "Emma Vaughan",
    "Kwong-Ning Chan",
    "Leonardo",
    "Liz Waight",
    "Lottie Bovingdon",
    "Michellie Young",
    "Poppy Michell",
    "Robert Goldie",
    "Sandy McNicol",
    "Simon Chan",
    "Svenja Noack",
    "Sydney Jeffers",
    "Linda Enstein",
]
# persons with names from the list above get price £25
discount_persons = {name.strip().lower():25 for name in salty_persons}

# first 15 get price £25
discount_amounts = {15:25, 25:35}

discount_keys = {'both_recipes': 30}


event.products.append(
    products.RegularPartnerWorkshop(
        name='Spinach - boost your shag',
        info='In these two hours we\'ll look at some energetic combos, '
             'revisit some standard moves and show you some interesting variations for them.',
        max_available=25,
        ratio=1.4,
        allow_first=10,
        price=35,
        workshop_date='17-September-2017',
        workshop_time='11:00 till 13:15, workshop time: 2h',
        workshop_level='Improvers/Intermediate',
        workshop_price='First 15 - £25 per person, then £35',
        workshop_location='Studio 3, Factory Studios, 407 Hornsey Rd., N194DX',
        discount_prices=json.dumps(discount_keys),
        discount_persons=json.dumps(discount_persons),
        discount_amounts=json.dumps(discount_amounts)
    ).model
)
event.products.append(
    products.RegularPartnerWorkshop(
        name='Olive oil - smooth your shag',
        info='These two hours will be all about dancing smoother, faster and more elegantly. '
             'We\'ll work on the basics to get you to hover over the dancefloor '
             'like Lenny Smith and combine moves with some fancy flows.',
        max_available=25,
        ratio=1.4,
        allow_first=10,
        price=35,
        workshop_date='17-September-2017',
        workshop_time='14:30 till 16:45, workshop time: 2h',
        workshop_level='Improvers/Intermediate',
        workshop_price='First 15 - £25 per person, then £35',
        workshop_location='Studio 3, Factory Studios, 407 Hornsey Rd., N194DX',
        discount_prices=json.dumps(discount_keys),
        discount_persons=json.dumps(discount_persons),
        discount_amounts=json.dumps(discount_amounts)
    ).model
)

database.db_session.commit()