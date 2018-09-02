import mongomock_mate
from datetime import datetime

import pytest
from mongoengine import connect
from salty_tickets.constants import LEADER, FOLLOWER, ACCEPTED, NEW, WAITING
from salty_tickets.dao import EventDocument, TicketsDAO, RegistrationDocument, RegistrationProductDetailsDocument
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct, PartyProduct


class TestTicketsDAO(TicketsDAO):
    def __init__(self):
        connect(host='mongomock://localhost')


@pytest.fixture
def test_dao():
    return TestTicketsDAO()

@pytest.fixture
def salty_recipes(test_dao):
    event_meta = {
        'name': 'Salty Recipes',
        'info': 'Salty Recipes Shag Weekender with super duper teachers',
        'start_date': datetime(2018, 7, 10),
        'end_date': datetime(2018, 7, 11),
        'products': [
            WorkshopProduct(name='Saturday', base_price=25.0, max_available=10, ratio=1.2, allow_first=2, tags={'full'}),
            WorkshopProduct(name='Sunday', base_price=25.0, max_available=10, ratio=1.2, allow_first=2, tags={'full'}),
            PartyProduct('Party', base_price=10.0, max_available=50, tags={'full'}),
        ],
        'registrations': {
            'Chang Schultheis': {'saturday': (LEADER, ACCEPTED),
                                 'sunday': (LEADER, ACCEPTED),
                                 'party': (None, ACCEPTED)},
            'Brianna Mudd': {'saturday': (FOLLOWER, ACCEPTED),
                             'sunday': (FOLLOWER, ACCEPTED),
                             'party': (None, ACCEPTED)},
            'Zora Dawe': {'saturday': (FOLLOWER, ACCEPTED), 'party': (None, ACCEPTED)},
            'Sebrina Marler': {'saturday': (FOLLOWER, ACCEPTED), 'party': (None, ACCEPTED)},
            'Aliza Mathias': {'saturday': (FOLLOWER, ACCEPTED), 'party': (None, ACCEPTED)},
            'Yi Damon': {'saturday': (FOLLOWER, NEW), 'party': (None, ACCEPTED)},
            'Berta Sadowski': {'saturday': (FOLLOWER, WAITING), 'party': (None, ACCEPTED)},
            'Emerson Damiano': {'sunday': (LEADER, ACCEPTED), 'party': (None, ACCEPTED)},
            'Stevie Stumpf': {'sunday': (LEADER, ACCEPTED), 'party': (None, ACCEPTED)},
            'Albertine Segers': {'sunday': (FOLLOWER, ACCEPTED), 'party': (None, ACCEPTED)},
        },
        'couples': {
            'sunday': ('Stevie Stumpf', 'Albertine Segers'),
        },
        'orders': [
            {
                'name': 'Chang Schultheis',
            }
        ]
    }
    save_event_from_meta(event_meta)
    return event_meta


def save_event_from_meta(event_meta):
    new_event = EventDocument.from_dataclass(Event(
        name=event_meta['name'],
        start_date=event_meta['start_date'],
        end_date=event_meta['end_date'],
        info=event_meta['info'],
        products={p.key: p for p in event_meta['products']}
    ))
    new_event.save()

    registration_docs = {}

    for full_name, products in event_meta['registrations'].items():
        email = full_name.replace(' ', '.') + '@salty.co.uk'
        reg = RegistrationDocument(full_name=full_name, email=email, event=new_event)
        # add to event.product
        for p_key, details in products.items():
            dance_role, status = details
            kwargs = {'product_key': p_key, 'status': status}
            if dance_role:
                kwargs['dance_role'] = dance_role
            reg.products.append(RegistrationProductDetailsDocument(**kwargs))
        reg.save()
        registration_docs[reg.full_name] = reg

    # couples
    for prod_key, couples in event_meta['couples'].items():
        partner_registration = RegistrationDocument.objects(event=new_event, full_name=couples[1]).first()
        RegistrationDocument.objects(event=new_event, full_name=couples[0]).update(
            set__products__S__partner_registration=partner_registration)

        partner_registration = RegistrationDocument.objects(event=new_event, full_name=couples[0]).first()
        RegistrationDocument.objects(event=new_event, full_name=couples[1]).update(
            set__products__S__partner_registration=partner_registration)


def test_dao_get_event(test_dao, salty_recipes):
    event = test_dao.get_event_by_key('salty_recipes')
    assert event.name == salty_recipes['name']
    assert list(event.products.keys()) == [p.key for p in salty_recipes['products']]
    assert event.products['saturday'].name == salty_recipes['products'][0].name

    assert isinstance(event.products['saturday'], WorkshopProduct)
    assert isinstance(event.products['party'], PartyProduct)
    print(event.products['sunday'].registrations)


