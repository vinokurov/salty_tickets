import pandas as pd
from geopy import Nominatim
from salty_tickets import sql_models, database

PAYMENTS_CSV_PATH = '~/Downloads/payments.csv'

columns = ['id', 'Card Address Country', 'Card Address City']
df = pd.read_csv(PAYMENTS_CSV_PATH, encoding="ISO-8859-1")[columns].set_index('id')
geolocator = Nominatim()

for reg in sql_models.Registration.query.all():
    order = sql_models.Order.query.join(sql_models.OrderProduct, aliased=False). \
        join(sql_models.order_product_registrations_mapping, aliased=False). \
        filter_by(registration_id=reg.id).first()
    if order and order.payments:
        for payments in order.payments:
            if payments.stripe_charge_id in df.index:
                location_str = ' '.join(list(df.loc[payments.stripe_charge_id].dropna().values))
                # print(reg.name, '-', location_str)
                geolocator_reverse_data = geolocator.reverse(geolocator.geocode(location_str).point, language='en')
                city = geolocator_reverse_data.raw['address'].get('city')
                if not city:
                    city = geolocator_reverse_data.raw['address'].get('town')
                if not city:
                    city = geolocator_reverse_data.raw['address'].get('village')
                if not city:
                    city = geolocator_reverse_data.raw['address'].get('county')

                state = geolocator_reverse_data.raw['address'].get('state')
                country = geolocator_reverse_data.raw['address']['country']
                print(reg.name, '-', country, '-', state, '-', city)
                # print(geolocator_reverse_data.raw['address'])
                reg.country = country
                reg.state = state
                reg.city = city

database.db_session.commit()