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
    start_date=datetime.datetime(2017, 7, 29),
    event_type='dance'
)


# event = models.Event.query.first()
event.products.append(
    products.CouplesOnlyWorkshop(
        name='Saturday Aerials Workshop',
        info='Saturday aerials workshop with Pol & Sara. Duration: 2h. Registration for couples only. Price: £50 per couple',
        max_available=30,
        price=50,
        price_weekend=40,
        weekend_key='aerials'
    ).model
)
event.products.append(
    products.CouplesOnlyWorkshop(
        name='Sunday Aerials Workshop',
        info='Sunday aerials workshop with Pol & Sara. Duration: 2h. Registration for couples only. Price: £50 per couple',
        max_available=30,
        price=50,
        price_weekend=40,
        weekend_key='aerials'
    ).model
)
event.products.append(
    products.RegularPartnerWorkshop(
        name='Saturday Shag Workshop',
        info='Saturday shag workshop with Pol & Sara. Duration: 2h. Price: £25 per person',
        max_available=40,
        ratio=1.35,
        price=25,
        price_weekend=20,
        weekend_key='shag'
    ).model
)
event.products.append(
    products.RegularPartnerWorkshop(
        name='Sunday Shag Workshop',
        info='Sunday shag workshop with Pol & Sara. Duration: 2h. Price: £25 per person',
        max_available=40,
        ratio=1.35,
        price=25,
        price_weekend=20,
        weekend_key='shag'
    ).model
)
database.db_session.add(event)
database.db_session.commit()

simona_fundraising_event = models.Event(
    name='Simona De Leo Crowdfunding',
    start_date=datetime.datetime(2017, 5, 22),
    event_type='crowdfunding'
)
simona_fundraising_event.products.append(
    products.DonateProduct('Just Donate').model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Filming a music/dance video by Alexander Vinokurov',
        info='Here comes some info',
        price=50,
        max_available=2,
        img_src='rewards/video_vnkrv.jpg'
    ).model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Vintage dress from Petite Krystal',
        info='Here comes some info',
        price=40,
        max_available=3,
        img_src='rewards/vintage_dresses.jpg'
    ).model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Collegiate Shag private class with Patrick O\'Brien',
        info='Here comes some info',
        price=35,
        max_available=3,
        img_src="rewards/shag_private_patrick.jpg"
    ).model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Photoshoot by Alexander Vinokurov',
        info='Here comes some info',
        price=25,
        max_available=3,
        allow_select=1,
        img_src='rewards/photoshoot_vnkrv.jpg'
    ).model
)

database.db_session.add(simona_fundraising_event)
database.db_session.commit()

