from salty_tickets import sql_models
from salty_tickets import database

sql_models.Base.metadata.create_all(bind=database.engine)
database.db_session.commit()