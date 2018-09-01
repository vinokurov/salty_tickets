import datetime

from salty_tickets import database
from salty_tickets import sql_models
from salty_tickets import products
import json

# Delete existing products
event = sql_models.Event.query.filter_by(event_key='salty_recipes_with_pol_sara').one()

# Define new products

event.products.append(
    products.RegularPartnerWorkshop(
        name='Collegiate Shag Dessert',
        info='Bonus 1h Collegiate Shag track devoted to the special skill of taking part in competitions or jams. '
        'Pol and Sara are known for competing world wide and for organising the Europe\'s most prestigious Shag competitions at the Barcelona Shag Festival. '
        'They will work on the key aspects of performing in a Shag competition and share hints how to get prepared for the contests.',
        max_available=25,
        ratio=1.6,
        allow_first=10,
        price=10,
        workshop_date='30-July-2017',
        workshop_time='14:15 till 15:15, workshop time: 1h',
        workshop_level='Improvers/Intermediate and higher',
        workshop_price='£10 per person',
        workshop_location='ISTD2 Dance Studios, 346 Old St, EC1V9NQ'
    ).model
)

event.products[0].max_available = 0
event.products[1].max_available = 0

database.db_session.commit()