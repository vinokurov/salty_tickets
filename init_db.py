from salty_tickets import models
from salty_tickets import database
from salty_tickets import products
# from salty_tickets import app
import datetime

# database.db_session.drop_all()
models.Base.metadata.drop_all(bind=database.engine)
models.Base.metadata.create_all(bind=database.engine)
database.db_session.commit()

event = models.Event(
    name='Salty Recipes with Pol & Sara',
    start_date=datetime.datetime(2017, 7, 29)
)


# event = models.Event.query.first()
event.products.append(
    products.CouplesOnlyWorkshop(
        name='Saturday Aerials Workshop',
        info='Saturday aerials workshop with Pol & Sara. Duration: 2h. Registration for couples only. Price: £50 per couple',
        parameters_dict={'max_places': '30', 'base_price': '50', 'price_weekend': '40', 'weekend_key': 'aerials'}
    ).model
)
event.products.append(
    products.CouplesOnlyWorkshop(
        name='Sunday Aerials Workshop',
        info='Sunday aerials workshop with Pol & Sara. Duration: 2h. Registration for couples only. Price: £50 per couple',
        parameters_dict={'max_places': '30', 'base_price': '50', 'price_weekend': '40', 'weekend_key': 'aerials'}
    ).model
)
event.products.append(
    products.RegularPartnerWorkshop(
        name='Saturday Shag Workshop',
        info='Saturday shag workshop with Pol & Sara. Duration: 2h. Price: £25 per person',
        parameters_dict={'max_places': '30', 'ratio': '1.35', 'base_price': '25', 'price_weekend': '20', 'weekend_key': 'shag'}
    ).model
)
event.products.append(
    products.RegularPartnerWorkshop(
        name='Sunday Shag Workshop',
        info='Sunday shag workshop with Pol & Sara. Duration: 2h. Price: £25 per person',
        parameters_dict={'max_places': '30', 'ratio': '1.35', 'base_price': '25', 'price_weekend': '20', 'weekend_key': 'shag'}
    ).model
)
database.db_session.add(event)
database.db_session.commit()

