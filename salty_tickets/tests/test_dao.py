from datetime import datetime

import pytest
from salty_tickets.constants import LEADER, FOLLOWER, NEW, SUCCESSFUL, COUPLE
from salty_tickets.dao import EventDocument, RegistrationDocument, ProductRegistrationDocument, \
    PaymentDocument
from salty_tickets.models.event import Event
from salty_tickets.models.products import WorkshopProduct, PartyProduct
from salty_tickets.models.registrations import PersonInfo, ProductRegistration, Payment, PaymentStripeDetails
from salty_tickets.waiting_lists import RegistrationStats


def test_dao_get_event(test_dao, salty_recipes):
    event = test_dao.get_event_by_key('salty_recipes')
    assert event.name == salty_recipes.name
    assert list(event.products.keys()) == [p.key for p in salty_recipes.products]
    assert event.products['saturday'].name == salty_recipes.products[0].name

    assert isinstance(event.products['saturday'], WorkshopProduct)
    assert isinstance(event.products['party'], PartyProduct)

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
    event = test_dao.get_event_by_key('salty_recipes', False)
    registrations = test_dao.get_registrations_for_product(event, 'saturday')

    saturday_names = [key[0] for key in salty_recipes.registration_docs.keys() if key[1] == 'saturday']
    assert saturday_names == [r.person.full_name for r in registrations]

    LEN = len(registrations)
    event = test_dao.get_event_by_key('salty_recipes')
    assert LEN == len(test_dao.get_registrations_for_product(event, event.products['saturday']))

    event_doc = EventDocument.objects(key='salty_recipes').first()
    assert LEN == len(test_dao.get_registrations_for_product(event_doc, event_doc.products['saturday']))


def test_add_person(test_dao, salty_recipes):
    event = test_dao.get_event_by_key('salty_recipes', False)
    person = PersonInfo(full_name='Mr X', email='mr.x@email.com')
    test_dao.add_person(person, event=event)

    assert person.id is not None
    person_doc = RegistrationDocument.objects(id=person.id).first()
    assert person.full_name == person_doc.full_name
    assert person.email == person_doc.email
    assert person_doc.event.name == salty_recipes.name


def test_add_registration(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')
    event = test_dao.get_event_by_key('salty_recipes', False)

    registration = ProductRegistration(
        person=mr_x,
        partner=ms_y,
        registered_by=mr_x,
        dance_role=LEADER,
        product_key='saturday'
    )
    test_dao.add_registration(registration, event=event)
    assert registration.id
    registration_doc = ProductRegistrationDocument.objects(id=registration.id).first()
    assert mr_x.id == registration_doc.person.id
    assert mr_x.id == registration_doc.registered_by.id
    assert ms_y.id == registration_doc.partner.id


def test_add_multiple_registrations(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')
    event = test_dao.get_event_by_key('salty_recipes', False)

    registrations = [
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER,
                            product_key='saturday'),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER,
                            product_key='saturday'),
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER,
                            product_key='sunay'),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER,
                            product_key='sunday'),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='party'),
    ]
    for r in registrations:
        test_dao.add_registration(r, event=event)

    assert registrations[0].id
    registration_doc = ProductRegistrationDocument.objects(id=registrations[0].id).first()
    assert mr_x.id == registration_doc.person.id
    assert mr_x.id == registration_doc.registered_by.id
    assert ms_y.id == registration_doc.partner.id

    sat_registrations = test_dao.get_registrations_for_product(event, 'saturday')
    assert registrations[1] in sat_registrations
    assert registrations[0] == sat_registrations[-2]
    assert registrations[0].id == sat_registrations[-2].id
    assert mr_x == sat_registrations[-2].person
    assert mr_x.id == sat_registrations[-2].person.id


def test_dao_get_doc(test_dao, salty_recipes):
    event = test_dao._get_doc(EventDocument, 'salty_recipes')
    assert salty_recipes.name == event.name

    event = test_dao._get_doc(EventDocument, event.id)
    assert salty_recipes.name == event.name

    event = test_dao._get_doc(EventDocument, event.to_dataclass())
    assert salty_recipes.name == event.name

    assert event == test_dao._get_doc(EventDocument, event)

    with pytest.raises(ValueError):
        test_dao._get_doc(EventDocument, 10)


def test_add_retrieve_payments(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')
    event = test_dao.get_event_by_key('salty_recipes', False)

    registrations = [
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER,
                            product_key='sunay', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER,
                            product_key='sunday', price=25, paid=25),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='party', price=5, paid=5),
    ]

    for r in registrations:
        test_dao.add_registration(r, event=event)

    payment = Payment(price=105, paid_by=mr_x, transaction_fee=1.5, registrations=registrations, status=NEW,
                      date=datetime(2018, 9, 3, 17, 0))

    test_dao.add_payment(payment, event)
    assert payment.id
    doc = PaymentDocument.objects(id=payment.id).first()

    mr_x_payments = test_dao.get_payments_by_person(event, mr_x)
    assert payment.id == mr_x_payments[0].id
    assert payment == mr_x_payments[0]


def test_add_retrieve_payments_auto_regester(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')
    event = test_dao.get_event_by_key('salty_recipes', False)

    registrations = [
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER,
                            product_key='sunay', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=LEADER,
                            product_key='sunday', price=25, paid=25),
        ProductRegistration(person=mr_x, registered_by=mr_x, product_key='party', price=5, paid=5),
    ]

    payment = Payment(price=105, paid_by=mr_x, transaction_fee=1.5, registrations=registrations, status=NEW,
                      date=datetime(2018, 9, 3, 17, 0))

    test_dao.add_payment(payment, event, register=True)
    assert payment.id
    doc = PaymentDocument.objects(id=payment.id).first()

    mr_x_payments = test_dao.get_payments_by_person(event, mr_x)
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
    event = test_dao.get_event_by_key('salty_recipes', False)

    registrations = [
        ProductRegistration(person=mr_x, partner=ms_y, registered_by=mr_x, dance_role=LEADER, active=False,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=ms_y, partner=mr_x, registered_by=mr_x, dance_role=FOLLOWER, active=False,
                            product_key='saturday', price=25, paid=25),
    ]
    payment = Payment(price=105, paid_by=mr_x, transaction_fee=1.5, registrations=registrations, status=NEW,
                      date=datetime(2018, 9, 3, 17, 0))

    # add NEW registration and payments
    test_dao.add_payment(payment, event, register=True)

    saved_payment = test_dao.get_payments_by_person(event, mr_x)[0]
    assert NEW == saved_payment.status

    # payment has been successful -> update payment status
    saved_payment.status = SUCCESSFUL
    test_dao.update_payment(saved_payment)
    assert SUCCESSFUL == test_dao.get_payments_by_person(event, mr_x)[0].status

    # update registrations to active
    for reg in saved_payment.registrations:
        reg.active
        test_dao.update_registration(reg)

    saved_registrations = test_dao.get_registrations_for_product(event, 'saturday')
    assert saved_registrations[-1] == saved_payment.registrations[-1]
    assert saved_registrations[-2] == saved_payment.registrations[-2]
    assert saved_registrations[-2].id == saved_payment.registrations[-2].id


def test_dao_mark_registrations_as_couple(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    ms_y = PersonInfo(full_name='Ms Y', email='ms.y@my.com')
    event = test_dao.get_event_by_key('salty_recipes', False)

    registrations = [
        ProductRegistration(person=mr_x, registered_by=mr_x, dance_role=LEADER, active=False,
                            product_key='saturday', price=25, paid=25),
        ProductRegistration(person=ms_y, registered_by=ms_y, dance_role=FOLLOWER, active=False,
                            product_key='saturday', price=25, paid=25),
    ]
    for r in registrations:
        test_dao.add_registration(r, event=event)

    assert registrations[0].partner is None
    assert registrations[1].partner is None

    test_dao.mark_registrations_as_couple(registrations[0], registrations[1])

    assert ms_y == registrations[0].partner
    assert mr_x == registrations[1].partner


def test_dao_query_registrations(test_dao, salty_recipes):
    person_0 = RegistrationDocument.objects(full_name='Chang Schultheis').first()

    registrations = test_dao.query_registrations('salty_recipes', person=person_0)
    expected = [('Chang Schultheis', 'saturday'), ('Chang Schultheis', 'sunday'), ('Chang Schultheis', 'party')]
    assert expected == [(r.person.full_name, r.product_key) for r in registrations]

    registrations = test_dao.query_registrations('salty_recipes', person=person_0, product='saturday')
    assert [('Chang Schultheis', 'saturday')] == [(r.person.full_name, r.product_key) for r in registrations]


def test_get_payment_event(test_dao, salty_recipes):
    payment = PaymentDocument.objects().order_by('-_id').first().to_dataclass()

    expected = test_dao.get_event_by_key('salty_recipes')
    assert expected == test_dao.get_payment_event(payment)

    expected = test_dao.get_event_by_key('salty_recipes', get_registrations=False)
    assert expected == test_dao.get_payment_event(payment, get_registrations=False)


def test_get_payments_with_stripe_details(test_dao, salty_recipes):
    mr_x = PersonInfo(full_name='Mr X', email='mr.x@my.com')
    event = test_dao.get_event_by_key('salty_recipes', False)
    payment = Payment(price=105, paid_by=mr_x, transaction_fee=1.5,
                      registrations=[
                            ProductRegistration(person=mr_x, registered_by=mr_x, dance_role=LEADER,
                                                product_key='saturday', price=25, paid=25),
                        ],
                      status=NEW, date=datetime(2018, 9, 3, 17, 0))
    test_dao.add_payment(payment, event, register=True)

    assert test_dao.get_payment_by_id(payment.id).stripe is None

    stripe_details = PaymentStripeDetails(token_id='toc_123', charges=['ch_123'])
    payment.stripe = stripe_details
    test_dao.update_payment(payment)

    assert stripe_details == PaymentDocument.objects(id=payment.id).first().stripe.to_dataclass()
    assert stripe_details == test_dao.get_payment_by_id(payment.id).stripe


