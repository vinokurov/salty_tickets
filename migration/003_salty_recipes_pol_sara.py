import datetime

from salty_tickets import database
from salty_tickets import models
from salty_tickets import products
import json

# Delete existing products
event = models.Event.query.filter_by(event_key='salty_recipes_with_pol_sara').one()
for product in event.products:
    database.db_session.delete(product)

database.db_session.commit()


# Define new products

event.products.append(
    products.CouplesOnlyWorkshop(
        name='Aerials Workshop - Morning',
        info='Saturday morning aerials workshop with Pol & Sara. Duration: 2h. Intermediate level Registration for couples only. Price: £80 per couple',
        max_available=10,
        price=50,
        discount_prices='{"aerials_full_day": 40}',
        workshop_date='29-July-2017',
        workshop_time='10:00 till 12:30',
        workshop_level='Improvers/Intermediate'
    ).model
)

event.products.append(
    products.CouplesOnlyWorkshop(
        name='Aerials Workshop - Afternoon',
        info='Saturday aerials workshop with Pol & Sara. Duration: 4h. Intermediate level Registration for couples only. Price: £80 per couple',
        max_available=10,
        price=50,
        discount_prices='{"aerials_full_day": 40}',
        workshop_date='29-July-2017',
        workshop_time='14:00 till 16:30',
        workshop_level='Intermediate and higher'
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Shag Workshop',
        info='Sunday shag workshop with Pol & Sara. Duration: 4h. Intermediate level. Price: £40 per person',
        max_available=40,
        ratio=1.35,
        # allow_first=10,
        price=40,
        workshop_date='30-July-2017',
        workshop_time='10:00 till 15:30',
        workshop_level='Improvers/Intermediate and higher'
    ).model
)

database.db_session.commit()