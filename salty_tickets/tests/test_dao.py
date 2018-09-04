import mongomock_mate
from datetime import datetime

import pytest
from mongoengine import connect
from salty_tickets.constants import LEADER, FOLLOWER, ACCEPTED, NEW, WAITING, SUCCESSFUL, FAILED, COUPLE
from salty_tickets.dao import EventDocument, TicketsDAO, RegistrationDocument, ProductRegistrationDocument, \
    PaymentDocument
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct, PartyProduct
from salty_tickets.models.registrations import PersonInfo, ProductRegistration, Payment
from salty_tickets.waiting_lists import RegistrationStats


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
                            event=new_event, paid_by=registration_docs[full_name]).save()

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
    assert isinstance(event.products['saturday'], WorkshopProduct)

    assert event.products['saturday'].waiting_list.registration_stats == {
        LEADER: RegistrationStats(accepted=1, waiting=0),
        FOLLOWER: RegistrationStats(accepted=4, waiting=1),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }

    assert event.products['sunday'].waiting_list.registration_stats == {
        LEADER: RegistrationStats(accepted=3, waiting=0),
        FOLLOWER: RegistrationStats(accepted=2, waiting=0),
        COUPLE: RegistrationStats(accepted=2, waiting=0)
    }


def test_dao_get_registrations_for_product(test_dao, salty_recipes):
    registrations = test_dao.get_registrations_for_product('salty_recipes', 'saturday')

    saturday_names = [name for name, det in salty_recipes['registrations'].items() if 'saturday' in det]
    assert [r.person.full_name for r in registrations] == saturday_names

    LEN = len(registrations)
    event = test_dao.get_event_by_key('salty_recipes')
    assert LEN == len(test_dao.get_registrations_for_product(event, event.products['saturday']))

    event_doc = EventDocument.objects(key='salty_recipes').first()
    assert LEN == len(test_dao.get_registrations_for_product(event_doc, event_doc.products['saturday']))


def test_add_person(test_dao, salty_recipes):
    person = PersonInfo(full_name='Mr X', email='mr.x@email.com')
    test_dao.add_person(person, event='salty_recipes')

    assert person.id is not None
    person_doc = RegistrationDocument.objects(id=person.id).first()
    assert person.full_name == person_doc.full_name
    assert person.email == person_doc.email
    assert person_doc.event.name == salty_recipes['name']


def test_add_registration(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')

    registration = ProductRegistration(
        person=mr_x,
        partner=ms_y,
        registered_by=mr_x,
        dance_role=LEADER,
        status=ACCEPTED,
        product_key='saturday'
    )
    test_dao.add_registration(registration, event='salty_recipes')
    assert registration.id
    registration_doc = ProductRegistrationDocument.objects(id=registration.id).first()
    assert mr_x.id == registration_doc.person.id
    assert mr_x.id == registration_doc.registered_by.id
    assert ms_y.id == registration_doc.partner.id


def test_add_multiple_registrations(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')

    registrations = [
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='saturday'),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='saturday'),
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='sunay'),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='sunday'),
        ProductRegistration(person=mr_x, registered_by=mr_x, status=ACCEPTED, product_key='party'),
    ]
    for r in registrations:
        test_dao.add_registration(r, event='salty_recipes')

    assert registrations[0].id
    registration_doc = ProductRegistrationDocument.objects(id=registrations[0].id).first()
    assert mr_x.id == registration_doc.person.id
    assert mr_x.id == registration_doc.registered_by.id
    assert ms_y.id == registration_doc.partner.id

    sat_registrations = test_dao.get_registrations_for_product('salty_recipes', 'saturday')
    assert registrations[1] in sat_registrations
    assert registrations[0] == sat_registrations[-2]
    assert registrations[0].id == sat_registrations[-2].id
    assert mr_x == sat_registrations[-2].person
    assert mr_x.id == sat_registrations[-2].person.id


def test_dao_get_doc(test_dao, salty_recipes):
    event = test_dao._get_doc(EventDocument, 'salty_recipes')
    assert event.name == salty_recipes['name']

    event = test_dao._get_doc(EventDocument, event.id)
    assert event.name == salty_recipes['name']

    event = test_dao._get_doc(EventDocument, event.to_dataclass())
    assert event.name == salty_recipes['name']

    assert event == test_dao._get_doc(EventDocument, event)

    with pytest.raises(ValueError):
        test_dao._get_doc(EventDocument, 10)


def test_add_retrieve_payments(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')

    registrations = [
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='sunay', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='sunday', price=25, paid=25),
        ProductRegistration(person=mr_x, registered_by=mr_x, status=ACCEPTED, product_key='party', price=5, paid=5),
    ]

    for r in registrations:
        test_dao.add_registration(r, event='salty_recipes')

    payment = Payment(price=105, paid_by=mr_x, transaction_fee=1.5, registrations=registrations, status=NEW,
                      date=datetime(2018, 9, 3, 17, 0))

    test_dao.add_payment(payment, 'salty_recipes')
    assert payment.id
    print(payment.id)
    doc = PaymentDocument.objects(id=payment.id).first()
    print(doc, doc.event, doc.paid_by)

    mr_x_payments = test_dao.get_payments_by_person('salty_recipes', mr_x)
    assert payment.id == mr_x_payments[0].id
    assert payment == mr_x_payments[0]


def test_add_retrieve_payments_auto_regester(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')

    registrations = [
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='sunay', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER, status=ACCEPTED,
                            product_key='sunday', price=25, paid=25),
        ProductRegistration(person=mr_x, registered_by=mr_x, status=ACCEPTED, product_key='party', price=5, paid=5),
    ]

    payment = Payment(price=105, paid_by=mr_x, transaction_fee=1.5, registrations=registrations, status=NEW,
                      date=datetime(2018, 9, 3, 17, 0))

    test_dao.add_payment(payment, 'salty_recipes', register=True)
    assert payment.id
    doc = PaymentDocument.objects(id=payment.id).first()

    mr_x_payments = test_dao.get_payments_by_person('salty_recipes', mr_x)
    assert payment.id == mr_x_payments[0].id
    assert payment == mr_x_payments[0]


def test_dao_update_doc(test_dao, salty_recipes):
    person = RegistrationDocument.objects(full_name='Yi Damon').first().to_dataclass()
    person.email = 'aaa@sss.ddd'
    person.comment = 'Some Comment'
    person.location = {'country': 'UK', 'city': 'London'}
    test_dao._update_doc(RegistrationDocument, person)

    person_1 = RegistrationDocument.objects(full_name='Yi Damon').first().to_dataclass()
    assert person == person_1


def test_update_statuses(test_dao, salty_recipes):
    """Here we test DAO methods to update entities on a real use case"""

    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')

    registrations = [
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER, status=NEW,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=FOLLOWER, status=NEW,
                            product_key='saturday', price=25, paid=25),
    ]
    payment = Payment(price=105, paid_by=mr_x, transaction_fee=1.5, registrations=registrations, status=NEW,
                      date=datetime(2018, 9, 3, 17, 0))

    # add NEW registration and payments
    test_dao.add_payment(payment, 'salty_recipes', register=True)

    saved_payment = test_dao.get_payments_by_person('salty_recipes', mr_x)[0]
    assert saved_payment.status == NEW

    # payment has been successful -> update payment status
    saved_payment.status = SUCCESSFUL
    print(saved_payment.id)
    test_dao.update_payment(saved_payment)
    assert test_dao.get_payments_by_person('salty_recipes', mr_x)[0].status == SUCCESSFUL

    # update registrations statuses to ACCEPTED
    for reg in saved_payment.registrations:
        reg.status = ACCEPTED
        test_dao.update_registration(reg)

    saved_registrations = test_dao.get_registrations_for_product('salty_recipes', 'saturday')
    assert saved_registrations[-1] == saved_payment.registrations[-1]
    assert saved_registrations[-2] == saved_payment.registrations[-2]
    assert saved_registrations[-2].id == saved_payment.registrations[-2].id


def test_dao_mark_registrations_as_couple(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')

    registrations = [
        ProductRegistration(person=mr_x, registered_by=mr_x, dance_role=LEADER, status=NEW,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=ms_y, registered_by=ms_y, dance_role=FOLLOWER, status=NEW,
                            product_key='saturday', price=25, paid=25),
    ]
    for r in registrations:
        test_dao.add_registration(r, event='salty_recipes')

    assert registrations[0].partner is None
    assert registrations[1].partner is None

    test_dao.mark_registrations_as_couple(registrations[0], registrations[1])

    assert registrations[0].partner == ms_y
    assert registrations[1].partner == mr_x

    assert test_dao.ge


def test_dao_query_registrations(test_dao, salty_recipes):
    person_0 = RegistrationDocument.objects(full_name='Chang Schultheis').first()

    registrations = test_dao.query_registrations('salty_recipes', person=person_0)
    assert [(r.person.full_name, r.product_key) for r in registrations] == [('Chang Schultheis', 'saturday'), ('Chang Schultheis', 'sunday'), ('Chang Schultheis', 'party')]

    registrations = test_dao.query_registrations('salty_recipes', person=person_0, product='saturday')
    assert [(r.person.full_name, r.product_key) for r in registrations] == [('Chang Schultheis', 'saturday')]

