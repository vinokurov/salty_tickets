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
        name='Aerials Breakfast',
        info='Saturday morning aerials workshop with Pol & Sara. Duration: 2h. Intermediate level. '
             'We allow signs up with partners only.',
        max_available=20,
        price=25,
        discount_prices='{"aerials_full_day": 20}',
        workshop_date='29-July-2017',
        workshop_time='10:30 till 13:00, workshop time: 2h',
        workshop_level='Improvers/Intermediate',
        workshop_price='£25 per person, £20 if book both aerial workshops'
    ).model
)

event.products.append(
    products.CouplesOnlyWorkshop(
        name='Aerials Lunch',
        info='Saturday morning aerials workshop with Pol & Sara. Duration: 2h. Intermediate level. '
             'We allow signs up with partners only.',
        max_available=20,
        price=25,
        discount_prices='{"aerials_full_day": 20}',
        workshop_date='29-July-2017',
        workshop_time='14:30 till 17:00, workshop time: 2h',
        workshop_level='Intermediate and higher',
        workshop_price='£25 per person, £20 if book both aerial workshops'
    ).model
)

event.products.append(
    products.RegularPartnerWorkshop(
        name='Collegiate Shag',
        info='Sunday shag workshop with Pol & Sara. Duration: 3h. Intermediate level. Price: £35 per person',
        max_available=35,
        ratio=1.35,
        allow_first=10,
        price=35,
        workshop_date='30-July-2017',
        workshop_time='10:00 till 14:00, workshop time: 3h',
        workshop_level='Improvers/Intermediate and higher',
        workshop_price='£35 per person'
    ).model
)

database.db_session.commit()