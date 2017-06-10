from salty_tickets import database

sql = """
ALTER TABLE events MODIFY event_key varchar(255);
ALTER TABLE events MODIFY name varchar(255);
ALTER TABLE products MODIFY name varchar(255);
ALTER TABLE product_parameters MODIFY parameter_name varchar(255);
ALTER TABLE product_parameters MODIFY parameter_value varchar(255);
ALTER TABLE registrations MODIFY name varchar(255);
ALTER TABLE registrations MODIFY email varchar(255);
ALTER TABLE order_product_details MODIFY field_name varchar(255);
ALTER TABLE order_product_details MODIFY field_value varchar(255);
"""

database.db_session.execute(sql)
# database.db_session.execute('ALTER TABLE events MODIFY event_key varchar(255)')

database.db_session.commit()