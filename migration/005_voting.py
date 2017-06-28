from salty_tickets import models
from salty_tickets import database

models.Base.metadata.create_all(bind=database.engine)
database.db_session.commit()