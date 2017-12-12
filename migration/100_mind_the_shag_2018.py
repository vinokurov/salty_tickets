import json
import datetime

from salty_tickets import database
from salty_tickets import models
from salty_tickets import products

event = models.Event(
    name='Mind The Shag 2018',
    start_date=datetime.datetime(2018, 4, 6),
    event_type='dance'
)

ARGS_BLOCK = {
    'ratio':1.4,
    'price':30,
    'discount_prices': json.dumps({'extra_block':25}),
    'allow_first':5,
    'waiting_list_price':5,
}
ARGS_STD1 = {'max_available':45, 'workshop_location':'Studio 1'}
ARGS_STD2 = {'max_available':35, 'workshop_location':'Studio 2'}
ARGS_STD3 = {'max_available':25, 'workshop_location':'Studio 3'}

event.products.append(
    products.RegularPartnerWorkshop(
        name='St.Louis Shag Essence',
        info='What makes it St. Louis Shag? Learn the basics of this dance, as well as traditional moves like kick-aways, sliding doors, and more.',
        workshop_date='7-April-2018',
        workshop_time='10:30-12:30',
        workshop_level='Jitterbug, St.Louis',
        workshop_teachers='Christian & Jenny',
        keywords='stl_fast_train',
        **ARGS_BLOCK, **ARGS_STD2,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Christian & Jenny\'s Original Shag Moves',
        info='Go on an adventure with us as we show you some of our favorite inventions in St. Louis Shag',
        workshop_date='8-April-2018',
        workshop_time='13:30-15:30',
        workshop_level='St.Louis',
        workshop_teachers='Christian & Jenny',
        keywords='stl_fast_train',
        **ARGS_BLOCK, **ARGS_STD1,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Swing Out Like You\'re From St. Louis',
        info='Workshop the three-wall swingout in the style of the 1940s St. Louis Jitterbugs, and then other quintessential regional variations',
        workshop_date='8-April-2018',
        workshop_time='10:30-12:30',
        workshop_level='Jitterbug',
        workshop_teachers='Christian & Jenny',
        **ARGS_BLOCK, **ARGS_STD3,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Superman Circle Pit',
        info='Learn Superman variations, spins from closed and open position, how to move around the floor and how to combine these tricks smoothly with your other Shag steps and patterns like there is no tomorrow.',
        workshop_date='7-April-2018',
        workshop_time='13:30-15:30',
        workshop_level='Collegiate Super',
        workshop_teachers='Pol & Sara',
        **ARGS_BLOCK, **ARGS_STD3,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Flea Hops & Tricks',
        info='Learn some easy mini aerials and tricks and how to integrate them into your Shag dancing from  from the masters.',
        workshop_date='7-April-2018',
        workshop_time='10:30-12:30',
        workshop_level='Collegiate Super',
        workshop_teachers='Pol & Sara',
        **ARGS_BLOCK, **ARGS_STD3,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Rhythm Shag',
        info='Make your dancing and choreographies pop by learning how to transition from a small move to a large move and vice versa, add contrasting footwork variations and hit those rhythms and breaks.',
        workshop_date='8-April-2018',
        workshop_time='13:30-15:30',
        workshop_level='Collegiate',
        workshop_teachers='Pol & Sara',
        **ARGS_BLOCK, **ARGS_STD3,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Rising Shag',
        info='Continue your journey with Pol & Sara, Peter & Aila to make you a Rising Star of Shag.',
        workshop_date='7-April-2018',
        workshop_time='16:30-18:30',
        workshop_level='Jitterbug,Collegiate',
        workshop_teachers='Pol & Sara, Peter & Aila',
        keywords='collegiate_fast_train',
        **ARGS_BLOCK, **ARGS_STD1,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Rockabilly Bopper Shag',
        info='Learn how to dance to Rockabilly Boppers and learn a short choreography to learn musicality.',
        workshop_date='8-April-2018',
        workshop_time='16:30-18:30',
        workshop_level='Collegiate',
        workshop_teachers='Patrick & Fancy',
        **ARGS_BLOCK, **ARGS_STD2,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Momentum Madness',
        info='Master the Shag whip and everything that needs counterbalance.',
        workshop_date='8-April-2018',
        workshop_time='16:30-18:30',
        workshop_level='Collegiate',
        workshop_teachers='Patrick & Fancy',
        **ARGS_BLOCK, **ARGS_STD3,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Shag Roots',
        info='You\'ve been Swing dancing for a good while, but you want to get in on the Shag fun? This level is for you. We will start with the basics, but will move on quickly to get you shagging in no time.',
        workshop_date='7-April-2018',
        workshop_time='13:30-15:30',
        workshop_level='Jitterbug,Collegiate',
        workshop_teachers='Patrick & Fancy',
        keywords='collegiate_fast_train',
        **ARGS_BLOCK, **ARGS_STD1,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Pocket Rocket Shag',
        info='Shag doesn\'t have to be huge! By focusing on the little things we can make a big difference to our dancing. The "Pocket Rocket" class looks at widening the tonal range of people\'s dancing with shag that is both chilled and compact - ideal for a long night of fast music on a crowded dance floor.',
        workshop_date='7-April-2018',
        workshop_time='13:30-15:30',
        workshop_level='Collegiate',
        workshop_teachers='Peter & Aila',
        **ARGS_BLOCK, **ARGS_STD2,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Phony Boy',
        info='This recently released classic clip is stuffed with fantastic material and styling, and we\'ve selected some of our favourite pieces to explore.',
        workshop_date='8-April-2018',
        workshop_time='16:30-18:30',
        workshop_level='Collegiate Super',
        workshop_teachers='Peter & Aila',
        **ARGS_BLOCK, **ARGS_STD2,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Tandem Time',
        info='This class will help you perfect and add flair to the tandem basic, with entrances, exits, and variations.',
        workshop_date='8-April-2018',
        workshop_time='13:30-15:30',
        workshop_level='Collegiate',
        workshop_teachers='Peter & Aila',
        **ARGS_BLOCK, **ARGS_STD2,
    ).model
)


#### PARTIES

event.products.append(
    products.FestivalPartyProduct(
        name='Friday Party',
        info='',
        price=15,
        max_available=150,
        party_date='6-April-2017',
        party_time='TBD',
        party_location='TBD',
        keywords='parties',
    ).model
)

event.products.append(
    products.FestivalPartyProduct(
        name='Saturday Party',
        info='',
        price=20,
        max_available=200,
        party_date='7-April-2017',
        party_time='TBD',
        party_location='TBD',
        keywords='parties',
    ).model
)

event.products.append(
    products.FestivalPartyProduct(
        name='Sunday Party',
        info='',
        price=15,
        max_available=150,
        party_date='8-April-2017',
        party_time='TBD',
        party_location='TBD',
        keywords='parties',
    ).model
)


###### WEEKEND PASSES

event.products.append(
    products.FestivalTrackProduct(
        max_available=150,
        name='Full Weekend Ticket',
        info='Includes 3 any stations and all parties. Also gives discount for additional stations',
        price=120,
        classes_to_chose=3,
        includes='parties'
    ).model
)

event.products.append(
    products.FestivalTrackProduct(
        max_available=150,
        name='Full Weekend Ticket, no Parties',
        info='Includes 3 any stations. Also gives discount for additional stations',
        price=120,
        classes_to_chose=3,
        includes=''
    ).model
)

event.products.append(
    products.FestivalTrackProduct(
        max_available=150,
        name='All parties',
        info='Includes all 3 parties. No classes included.',
        price=45,
        classes_to_chose=0,
        includes='parties'
    ).model
)

event.products.append(
    products.FestivalTrackProduct(
        max_available=45,
        name='Fast Train to Collegiate Shag',
        info='Includes 2 stations for learning Collegiate Shag and all parties. Also gives discount for additional stations',
        price=90,
        classes_to_chose=0,
        includes='collegiate_fast_train,parties'
    ).model
)

event.products.append(
    products.FestivalTrackProduct(
        max_available=45,
        name='Fast Train to Collegiate Shag, no Parties',
        info='Includes 2 stations for learning Collegiate Shag. Also gives discount for additional stations',
        price=55,
        classes_to_chose=0,
        includes='collegiate_fast_train'
    ).model
)

event.products.append(
    products.FestivalTrackProduct(
        max_available=35,
        name='Fast Train to St.Louis Shag',
        info='Includes 2 stations for learning St.Louis Shag and all parties. Also gives discount for additional stations',
        price=90,
        classes_to_chose=0,
        includes='stl_fast_train,parties'
    ).model
)

event.products.append(
    products.FestivalTrackProduct(
        max_available=35,
        name='Fast Train to St.Louis Shag, no Parties',
        info='Includes 2 stations for learning St.Louis Shag. Also gives discount for additional stations',
        price=55,
        classes_to_chose=0,
        includes='stl_fast_train'
    ).model
)


database.db_session.add(event)
database.db_session.commit()
