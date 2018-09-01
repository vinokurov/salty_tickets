from salty_tickets import database
from salty_tickets import sql_models

# Delete existing products
event = sql_models.Event.query.filter_by(event_key='salty_recipes_with_pol_sara').one()
for product in event.products:
    product.add_parameters({'workshop_location': 'ISTD2 Dance Studios, 346 Old St, EC1V9NQ'})

database.db_session.commit()