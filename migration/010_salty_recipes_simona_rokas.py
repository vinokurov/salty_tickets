import json
import datetime

from salty_tickets import database
from salty_tickets import sql_models
from salty_tickets import products

event = sql_models.Event.query.filter_by(event_key='salty_recipes_with_patrick_fancy').one()
event.active = False
database.db_session.commit()

event = sql_models.Event(
    name='Salty Recipes with Simona & Rokas',
    start_date=datetime.datetime(2017, 11, 26),
    event_type='dance'
)

# first 15 get price £25
discount_amounts = {15:25, 25:30, 30:35}

discount_keys = {'both_recipes': 30}


event.products.append(
    products.RegularPartnerWorkshop(
        max_available=30,
        name='Potato Pancakes - The Starter',
        info='Potatoes are truly king when it comes to Lithuanian food, '
             'as Simona & Rokas are the Royals in St. Louis Shag around Europe. '
             'This class will revise the basics and move on to a more complicated material. '
             'This is a perfect way to start your meal that will make you fall in love '
             'with St. Louis Shag, just like everyone loves potatoes!',
        ratio=1.4,
        allow_first=10,
        price=35,
        waiting_list_price=5,
        workshop_date='26-November-2017',
        workshop_time='11:00 till 13:15, workshop time: 2h',
        workshop_level='Improvers/Intermediate swing dancers, little or no St.Louis Shag experience',
        workshop_price='First 15 - £25 per person, next 10 - £30, then £35',
        workshop_location='Studio 2, Clean Break, 2 Patshull Road, London, NW5 2LB',
        discount_prices=json.dumps(discount_keys),
        discount_persons='salty_recipes_simona_rokas',
        discount_amounts=json.dumps(discount_amounts),
    ).model
)
event.products.append(
    products.RegularPartnerWorkshop(
        name='Zeppelins - Hot Adventures',
        info='Lithuania\'s famous cepelinai are large dumplings with resemblance to zeppelin airships. '
             'These crazy Lithuanians are flying to London to share their advanced moves and secrets '
             'that will make you fly away to the moon!',
        max_available=25,
        ratio=1.4,
        allow_first=10,
        price=35,
        waiting_list_price=5,
        workshop_date='26-November-2017',
        workshop_time='14:00 till 16:15, workshop time: 2h',
        workshop_level='Improvers/Intermediate St.Louis Shag dancers',
        workshop_price='First 15 - £25 per person, next 10 - £30, then £35',
        workshop_location='Studio 2, Clean Break, 2 Patshull Road, London, NW5 2LB',
        discount_prices=json.dumps(discount_keys),
        discount_persons='salty_recipes_simona_rokas',
        discount_amounts=json.dumps(discount_amounts),
    ).model
)

database.db_session.add(event)
database.db_session.commit()
