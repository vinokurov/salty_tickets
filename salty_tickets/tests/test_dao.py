import mongomock_mate
from datetime import datetime

import pytest
from mongoengine import connect
from salty_tickets.constants import LEADER, FOLLOWER, ACCEPTED, NEW, WAITING, SUCCESSFUL, FAILED
from salty_tickets.dao import EventDocument, TicketsDAO, RegistrationDocument, ProductRegistrationDocument, \
    PaymentDocument
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
            'Chang Schultheis': {'saturday': (LEADER, ACCEPTED, 20, 20),
                                 'sunday': (LEADER, ACCEPTED, 20, 20),
                                 'party': (None, ACCEPTED, 5, 5)},
            'Brianna Mudd': {'saturday': (FOLLOWER, ACCEPTED, 20, 20),
                             'sunday': (FOLLOWER, ACCEPTED, 20, 20),
                             'party': (None, ACCEPTED, 5, 5)},
            'Zora Dawe': {'saturday': (FOLLOWER, ACCEPTED, 25, 25), 'party': (None, ACCEPTED, 5, 5)},
            'Sebrina Marler': {'saturday': (FOLLOWER, ACCEPTED, 25, 25), 'party': (None, ACCEPTED, 5, 5)},
            'Aliza Mathias': {'saturday': (FOLLOWER, ACCEPTED, 25, 25), 'party': (None, ACCEPTED, 5, 5)},
            'Yi Damon': {'saturday': (FOLLOWER, NEW, 25, 0), 'party': (None, ACCEPTED, 5, 5)},
            'Berta Sadowski': {'saturday': (FOLLOWER, WAITING, 25, 10), 'party': (None, ACCEPTED, 5, 5)},
            'Emerson Damiano': {'sunday': (LEADER, ACCEPTED, 25, 25), 'party': (None, ACCEPTED, 5, 5)},
            'Stevie Stumpf': {'sunday': (LEADER, ACCEPTED, 25, 25), 'party': (None, ACCEPTED, 5, 5)},
            'Albertine Segers': {'sunday': (FOLLOWER, ACCEPTED, 25, 25), 'party': (None, ACCEPTED, 5, 5)},
        },
        'couples': {
            'sunday': ('Stevie Stumpf', 'Albertine Segers'),
        },
        'payments': {
            'Chang Schultheis': [(50, 1.5, SUCCESSFUL)],
            'Brianna Mudd': [(50, 1.5, SUCCESSFUL)],
            'Zora Dawe': [(35, 0.7, SUCCESSFUL)],
            'Sebrina Marler': [(35, 0.7, SUCCESSFUL)],
            'Aliza Mathias': [(35, 0.7, SUCCESSFUL)],
            'Yi Damon': [(25, 0.4, FAILED), (10, 0.3, SUCCESSFUL)],
            'Berta Sadowski': [(15, 0.4, SUCCESSFUL)],
            'Emerson Damiano': [(35, 0.7, SUCCESSFUL)],
            'Stevie Stumpf': [(70, 2.0, SUCCESSFUL)],
        },
        'registered_by': {
            'Albertine Segers': 'Stevie Stumpf',
        }
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
        reg.save()
        registration_docs[reg.full_name] = reg
        # add to event.product
        for p_key, details in products.items():
            dance_role, status, price, paid = details
            kwargs = {'product_key': p_key, 'status': status, 'price': price, 'paid': paid,
                      'event': new_event, 'person': reg, 'registered_by': reg}
            if dance_role:
                kwargs['dance_role'] = dance_role
            ProductRegistrationDocument(**kwargs).save()

    # couples
    for prod_key, couples in event_meta['couples'].items():
        partner_0 = RegistrationDocument.objects(event=new_event, full_name=couples[0]).first()
        partner_1 = RegistrationDocument.objects(event=new_event, full_name=couples[1]).first()

        ProductRegistrationDocument.objects(event=new_event, product_key=prod_key, person=partner_0).update(
            set__partner=partner_1)

        ProductRegistrationDocument.objects(event=new_event, product_key=prod_key, person=partner_1).update(
            set__partner=partner_0)

    for person, registerer in event_meta['registered_by'].items():
        registration_docs[person].registered_by = registration_docs[registerer]
        registration_docs[person].save()

    for full_name, payments in event_meta['payments'].items():
        for price, fee, status in payments:
            PaymentDocument(price=price, transaction_fee=fee, status=status,
                            event=new_event, payed_by=registration_docs[full_name]).save()

    event_meta['registration_ids'] = {name: reg.id for name, reg in registration_docs.items()}


def test_dao_get_event(test_dao, salty_recipes):
    event = test_dao.get_event_by_key('salty_recipes')
    assert event.name == salty_recipes['name']
    assert list(event.products.keys()) == [p.key for p in salty_recipes['products']]
    assert event.products['saturday'].name == salty_recipes['products'][0].name

    assert isinstance(event.products['saturday'], WorkshopProduct)
    assert isinstance(event.products['party'], PartyProduct)

    print(event.products['sunday'].registrations)
    assert event.id is not None
    for prod_key, product in event.products.items():
        for reg in product.registrations:
            assert reg.id is not None

    print(event.products['saturday'].waiting_list)

    # print(salty_recipes['registration_ids']['Stevie Stumpf'])
    # print([pr.to_dataclass() for pr in ProductRegistrationDocument.objects(person=salty_recipes['registration_ids']['Stevie Stumpf']).all()])


