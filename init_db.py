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
        name='Aerials Workshop',
        info='Sunday aerials workshop with Pol & Sara. Duration: 4h. Intermediate level Registration for couples only. Price: £80 per couple',
        max_available=15,
        price=80,
        weekend_key='aerials'
    ).model
)
event.products.append(
    products.RegularPartnerWorkshop(
        name='Saturday Shag Workshop',
        info='Saturday shag workshop with Pol & Sara. Duration: 4h. Intermediate level. Price: £40 per person',
        max_available=40,
        ratio=1.35,
        price=40,
        weekend_key='shag'
    ).model
)
database.db_session.add(event)
database.db_session.commit()

simona_fundraising_event = models.Event(
    name='Simona De Leo\'s Crowdfunding Campaign',
    start_date=datetime.datetime(2017, 5, 27),
    event_type='crowdfunding'
)
simona_fundraising_event.products.append(
    products.DonateProduct('Donate').model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Filming a music/dance video by Alexander Vinokurov',
        info='Feeling like Frank, Ginger & Fred, why don\'t you give a spin to your performance skills making a video. '
             'Alexander Vinokurov worked with London\'s dancers, venues, events\' competitions and performing troupes. '
             'Get a bespoke video for your dance project or a band. '
             'See more at  his <a href="https://www.youtube.com/channel/UC2VEJE8D1DIIaOC_jHyQHfA" target="_blank">YouTube channel<a>.',
        price=50,
        max_available=2,
        img_src='rewards/video_vnkrv.jpg'
    ).model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='La Petite Skirt - Vivien',
        info='<p><em>Size: 10/12</em></p>'
             '<p>La Petite is bespoke brand made in Italy. </p>'
             '<p>"Petite" is an adjective, a point of view, a working method. '
             'Small producers and artisans are the providers of the materials and making fully made in Italy. '
             'Short production chain, still relying on direct contact, on hand stalks, and endless coffee cups. '
             'Every garment is the story of a woman, every garment has his name embroidered on the label as it was on '
             'those handkerchiefs seen only in the hands of grandmothers.</p>',
        price=40,
        max_available=1,
        img_src='rewards/la_petite_vivien.jpg'
    ).model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='La Petite Skirt - Silvana',
        info='<p><em>Size: 10/12</em></p>'
             '<p>La Petite is bespoke brand made in Italy. </p>'
             '<p>"Petite" is an adjective, a point of view, a working method. '
             'Small producers and artisans are the providers of the materials and making fully made in Italy. '
             'Short production chain, still relying on direct contact, on hand stalks, and endless coffee cups. '
             'Every garment is the story of a woman, every garment has his name embroidered on the label as it was on '
             'those handkerchiefs seen only in the hands of grandmothers.</p>',
        price=40,
        max_available=1,
        img_src='rewards/la_petite_silvana.jpg'
    ).model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Collegiate Shag/Lindy Hop private class with Patrick O\'Brien',
        info='Patrick is known as an international dance teacher and has been at the forefront of the revival of Collegiate Shag and is an avid dancer. '
             'If you want to get to the next level with your dancing a private class with Patrick will get you there as the focus will be on you and you\'ll get immediate feedback.',
        price=35,
        max_available=3,
        allow_select=1,
        img_src="rewards/shag_private_patrick.jpg"
    ).model
)
simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Photoshoot by Alexander Vinokurov',
        info=''
             'Ever wanted a photoshoot for yourself book one for yourself or your dance troupe in a studio or outdoors'
             'A studio or an outdoor photo session, a nice and sweet or a crazy location. '
             'For your personal profile or a dance couple. Any idea!',
        price=25,
        max_available=3,
        allow_select=1,
        img_src='rewards/photoshoot_vnkrv.jpg'
    ).model
)

database.db_session.add(simona_fundraising_event)
database.db_session.commit()

