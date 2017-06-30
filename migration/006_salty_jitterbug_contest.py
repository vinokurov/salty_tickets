import datetime

from salty_tickets import database
from salty_tickets import models
from salty_tickets import products

event = models.Event(
    name='Salty Jitterbugs Contest 10/07',
    start_date=datetime.datetime(2017, 7, 10),
    event_type='dance'
)

database.db_session.add(event)

event.products.append(
    products.StrictlyContest(
        name='Contest Participation',
        info='The last Salty Monday of the season will feature the Salty Jitterbugs Contest. '
             'The format is "Showdown" where 2 competitor couples dance 8 bars of 8\'s '
             'and are judged as the better of the two, with one couple advancing immediately to the next round.'
             'The last 2 couples dance spotlights, then together.'
             'Music will be fast!'
             'Judging is performed by the audience via online voting.'
             'The winner couple gets tickets for Salty Recipes with Pol & Sara: '
             'either 1 session aerials for couple or 50% discount for shag for couple.',
        max_available=8,
        price=5,
        contest_date='10-July-2017',
        contest_time='22:00 till 22:15',
        contest_price='£5 per couple',
        contest_prize='Salty Recipes aerials couple ticket',
        contest_format='Strictly / Showdown',
        contest_level='No restrictions on level or style',
    )
)