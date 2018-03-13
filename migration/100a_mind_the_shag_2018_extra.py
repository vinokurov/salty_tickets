import json
import datetime

from salty_tickets import database
from salty_tickets import models
from salty_tickets import products

event = models.Event.query.filter_by(name='Mind The Shag 2018').one()

ARGS_BLOCK = {
    'ratio':1.4,
    'price':35,
    'discount_prices': json.dumps({'extra_block':30}),
    'allow_first':5,
    'waiting_list_price':5,
}
ARGS_STD1 = {'max_available':45, 'workshop_location':'Studio 1'}
ARGS_STD2 = {'max_available':35, 'workshop_location':'Studio 2'}
ARGS_STD3 = {'max_available':25, 'workshop_location':'Studio 3'}

event.products.append(
    products.RegularPartnerWorkshop(
        name='Musicality in Shag',
        info='At this station we\'ll be looking at how to dance with more musicality and how to adjust your dancing to the music.',
        workshop_date='8-April-2018',
        workshop_time='10:30-12:30',
        workshop_level='Collegiate',
        workshop_teachers='Patrick & Fancy',
        **ARGS_BLOCK, **ARGS_STD2,
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Kick It',
        info='Do you know how to enter the cross kicks? Now let\'s have some serious fun there! At this station we will learn as many variations of this step as possible from Pol & Sara and Peter & Aila.',
        workshop_date='7-April-2018',
        workshop_time='16:30-18:30',
        workshop_level='Collegiate',
        workshop_teachers='Pol & Sara, Peter & Aila',
        **ARGS_BLOCK, **ARGS_STD3,
    ).model
)

database.db_session.commit()
