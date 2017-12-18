from salty_tickets import database
from salty_tickets import models

sql = """
ALTER TABLE registrations ADD country varchar(255) DEFAULT NULL;
ALTER TABLE registrations ADD state varchar(255) DEFAULT NULL;
ALTER TABLE registrations ADD city varchar(255) DEFAULT NULL;
ALTER TABLE registrations ADD event_id int(11) DEFAULT NULL;
ALTER TABLE registrations ADD CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES events(id);
ALTER TABLE registrations ADD registration_group_id int(11) DEFAULT NULL;
ALTER TABLE registrations ADD CONSTRAINT fk_registration_group_id FOREIGN KEY (registration_group_id) REFERENCES registration_groups(id);
"""
database.db_session.execute(sql)
database.db_session.commit()

# fix registration.event_id links
for reg in models.Registration.query.all():
    order = models.Order.query.join(models.OrderProduct, aliased=False). \
        join(models.order_product_registrations_mapping, aliased=False). \
        filter_by(registration_id=reg.id).first()
    if order:
        reg.event_id = order.event_id

# fix registration_group_id
for rg in models.RegistrationGroup.query.all():
    for op in rg.signup_group.order_products:
        op.registrations[0].registration_group_id = rg.id

database.db_session.commit()
