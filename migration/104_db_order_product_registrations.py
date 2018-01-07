from salty_tickets import database

sql = """
ALTER TABLE order_products ADD registration_id int(11) DEFAULT NULL;
UPDATE order_products op set registration_id = 
    (SELECT registration_id from order_product_registrations_mapping oprm WHERE oprm.order_product_id=op.id); 
"""
database.db_session.execute(sql)
database.db_session.commit()