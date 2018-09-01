from datetime import datetime

from salty_tickets.forms import create_event_form, DanceSignupForm
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct


def test_get_registration_from_form():
    pass


def test_create_event_form():
    event = Event(name='Salty Recipes', key='salty_recipes',
                  start_date=datetime(2018, 10, 11, 10, 0), end_date=datetime(2018, 10, 11, 16, 0))

    event.append_products([
        WorkshopProduct(name='Morning WS', base_price=15.0, max_available=10, ratio=1.5, start_datetime=datetime(2018, 10, 11, 10, 0), end_datetime=datetime(2018, 10, 11, 12, 0)),
        WorkshopProduct(name='Evening WS', base_price=15.0, max_available=10, ratio=1.5, start_datetime=datetime(2018, 10, 11, 15, 0), end_datetime=datetime(2018, 10, 11, 16, 0)),
    ])

    form = create_event_form(event)
    assert issubclass(form, DanceSignupForm)
