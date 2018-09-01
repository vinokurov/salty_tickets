import datetime

from salty_tickets import database
from salty_tickets import sql_models
from salty_tickets import products

event = sql_models.Event(
    name='Salty Jitterbugs Contest 10/07',
    start_date=datetime.datetime(2017, 7, 10),
    event_type='dance'
)

database.db_session.add(event)

event.products.append(
    products.StrictlyContest(
        name='Salty Jitterbugs Contest',
        info='''
The last Salty Monday of the season will feature the Salty Jitterbugs Contest! 
We will have a "Showdown" format where 2 couples dance eight 8s with only one couple advancing immediately to the next round.
The last 2 couples dance spotlights, then all skates.
The music will be live and it will be fast! Any dance style goes!
Judging is performed by the audience via an online voting system.<br>

The winning couple will get tickets for our Salty Recipes workshop with Pol & Sara end of July: 
either 1 session of aerials as a couple or 50% discount for Shag as a couple.
        ''',
        max_available=8,
        price=5,
        contest_date='10-July-2017',
        contest_time='22:00 till 22:15',
        contest_price='£5 per couple',
        contest_prize='Salty Recipes tickets',
        contest_format='Strictly / Showdown',
        contest_level='No restrictions on level or style',
        contest_location='Salty Mondays / Far Rockaway Shoreditch, EC2A3BS',
    ).model
)

database.db_session.commit()