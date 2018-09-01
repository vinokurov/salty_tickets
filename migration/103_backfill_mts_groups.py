import pandas as pd
from salty_tickets import sql_models, database

df = pd.read_csv('~/Downloads/mts_registration_groups.csv')
for ix, row in df.iterrows():
    reg = sql_models.Registration.query.filter_by(id=row.registration_id).one()
    reg.registration_group_id = row.group_id
    database.db_session.commit()