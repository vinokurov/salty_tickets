import datetime

from salty_tickets import database
from salty_tickets import sql_models
from salty_tickets import products

simona_fundraising_event = sql_models.Event.query.filter_by(event_key='simona_de_leo_s_crowdfunding_campaign').one()

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='It\'s Summer',
        info='Original watercolor, size A3, not framed.',
        price=50,
        max_available=1,
        img_src='rewards/big/it_s_summer.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Mr. Wompls Dreams',
        info='Original watercolor, size A3, not framed.',
        price=50,
        max_available=1,
        img_src='rewards/big/mr_wompls_dreams.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Mr. Wompls on the Grass',
        info='Original watercolor, size A3, not framed.',
        price=50,
        max_available=1,
        img_src='rewards/big/mr_wompls_on_the_grass.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Mr. Wompls on the Moon',
        info='Original watercolor, size A3, not framed.',
        price=70,
        max_available=1,
        img_src='rewards/big/mr_wompls_on_the_moon.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='The Foxes Wedding',
        info='Original illustration, mixed media, size A3, not framed.',
        price=70,
        max_available=1,
        img_src='rewards/big/the_foxes_wedding.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='A Guitarist in Paris',
        info='Original sketch, size A4, not framed.',
        price=20,
        max_available=1,
        img_src='rewards/medium/a_guitarist_in_paris.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Singer',
        info='Original sketch, size A4, not framed.',
        price=20,
        max_available=1,
        img_src='rewards/medium/singer_sketch.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='The Guitarist',
        info='Original sketch, size A4, not framed.',
        price=20,
        max_available=1,
        img_src='rewards/medium/the_guitarist_sketch.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Charleston',
        info='Original mixed media, size A4, not framed.',
        price=30,
        max_available=1,
        img_src='rewards/medium/charleston.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Smell a Rose',
        info='Original mixed media, size A4, not framed.',
        price=30,
        max_available=1,
        img_src='rewards/medium/smell_a_rose.jpg'
    ).model
)

database.db_session.commit()