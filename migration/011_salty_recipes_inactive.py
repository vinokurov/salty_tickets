from salty_tickets import database
from salty_tickets import sql_models

event = sql_models.Event.query.filter_by(event_key='salty_recipes_with_simona_rokas').one()
event.active = False
database.db_session.commit()