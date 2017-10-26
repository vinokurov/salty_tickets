import datetime

from salty_tickets import database
from salty_tickets import models
from salty_tickets import products

simona_fundraising_event = models.Event.query.filter_by(event_key='simona_de_leo_s_crowdfunding_campaign').one()

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Cake from Robert Goldie',
        info='Craving cake, no time to bake? Then let renowned baker and DJ Robert pleasure '
             'your palate with a scrumptious slice of homemade heaven! Choose between Guinness '
             'cake with cream-cheese frosting, pistachio & cardamom with lemon icing, '
             'and chocolate & peanut butter with a melting middle.',
        price=15,
        max_available=3,
        img_src='rewards/robert_cake.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Poster from Helen Rimell',
        info='An original poster print by Helen Rimell from her latest Kashmir photo collection. Size - A3, not framed.',
        price=50,
        max_available=1,
        img_src='rewards/helen_poster.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Portrait from a photo - A3',
        info='An original gift for yourself or a friend, get a  portrait with the technique that you like the most, '
             'ink black&white, watercolor or pastels. size A3.',
        price=60,
        max_available=20,
        img_src='rewards/portrait_from_photo.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Portrait from a photo - A4',
        info='An original gift for yourself or a friend, get a  portrait with the technique that you like the most, '
             'ink black&white, watercolor or pastels. size A4.',
        price=30,
        max_available=20,
        img_src='rewards/portrait_from_photo.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Mr. Wompls Singer - A4',
        info='Original watercolor, pastels and ink, size A4, not framed.',
        price=40,
        max_available=1,
        img_src='rewards/whoopie_singer.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Get watercolored!',
        info='Get watercolored! You can commission an original watercolor of yourself or your favourite subject. A4 size',
        price=20,
        max_available=100,
        img_src='rewards/get_watercolored.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Mr. Wompls Dancer - A4',
        info='Original watercolor, pastels and ink, size A4, not framed. '
             'The work won the "quality prize" and was part of the exhibition '
             'at the illustration contest "scarpetta d\'oro" 2016, Venice, Italy',
        price=50,
        max_available=1,
        img_src='rewards/whoopie_dancer.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Mr. Wompls Dancer 2 - A4',
        info='Original watercolor, pastels and ink, size A4, not framed.',
        price=40,
        max_available=1,
        img_src='rewards/whoopie_dancer-2.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Get a graphic for promoting your band or event',
        info='Flyers, posters, banners, cards, tote bags, etc.. etc.',
        price=50,
        max_available=100,
        img_src='rewards/flyers.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Get your CD cover designed',
        info='Illustration and graphic design',
        price=150,
        max_available=100,
        img_src='rewards/cd_cover.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='T-shirt design',
        info='Design a T-shirt for your event. The price doesn\'t include printing',
        price=25,
        max_available=100,
        img_src='rewards/t_shirt.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='A6 cards',
        info='Simona De Leo art A6 printed cards',
        price=5,
        max_available=20,
        img_src='rewards/cards.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Private drawing class',
        info='Private drawing and color techniques lesson with Simona De Leo.',
        price=30,
        max_available=100,
        img_src='rewards/drawing_class.jpg'
    ).model
)

simona_fundraising_event.products.append(
    products.MarketingProduct(
        name='Original handmade greeting cards',
        info='Say something special with an original card, get your own personal illustration. A6 size.',
        price=10,
        max_available=100,
        img_src='rewards/greeting_card.jpg'
    ).model
)

database.db_session.commit()
