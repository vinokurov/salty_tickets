from datetime import datetime

from salty_tickets.models.products import WorkshopProduct, BaseProduct
from salty_tickets.models.registrations import Person, Registration
from salty_tickets.validators import errors_at_least_any_with_tag, errors_if_overlapping


def test_at_least_any_with_tag():
    products = {
        'w1': BaseProduct(name='W1', tags={'workshop'}),
        'w2': BaseProduct(name='W2', tags={'workshop'}),
        'w3': BaseProduct(name='W3', tags={'workshop'}),
        'p': BaseProduct(name='P', tags={'party'})
    }

    mr_x = Person(full_name='Mr.X', email='mr.x@x.com')
    ms_y = Person(full_name='Ms.Y', email='ms.y@y.com')

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, product_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, product_key='w2'),
    ]

    error_text = 'Not enough workshops'
    assert not errors_at_least_any_with_tag(registrations, products, 'workshop', 1, error_text)
    assert not errors_at_least_any_with_tag(registrations, products, 'workshop', 2, error_text)

    assert 'Not enough workshops' == errors_at_least_any_with_tag(registrations, products,
                                                                  'workshop', 3, error_text)

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, product_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, product_key='w2'),
        Registration(person=mr_x, registered_by=mr_x, product_key='w3'),
        Registration(person=ms_y, registered_by=mr_x, product_key='w1'),
        Registration(person=ms_y, registered_by=mr_x, product_key='w2'),
    ]

    assert not errors_at_least_any_with_tag(registrations, products, 'workshop', 2, error_text)
    assert 'Not enough workshops' == errors_at_least_any_with_tag(registrations, products,
                                                                  'workshop', 3, error_text)

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, product_key='p')
    ]

    assert not errors_at_least_any_with_tag(registrations, products, 'workshop', 2, error_text)


def test_non_overlapping():
    products = {
        'w1': WorkshopProduct(name='W1', tags={'workshop'}, start_datetime=datetime(2018, 9, 23, 11, 0)),
        'w2': WorkshopProduct(name='W2', tags={'workshop'}, start_datetime=datetime(2018, 9, 23, 11, 0)),
        'w3': WorkshopProduct(name='W3', tags={'workshop'}, start_datetime=datetime(2018, 9, 23, 16, 0)),
        'p': BaseProduct(name='P', tags={'party'})
    }

    mr_x = Person(full_name='Mr.X', email='mr.x@x.com')
    ms_y = Person(full_name='Ms.Y', email='ms.y@y.com')

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, product_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, product_key='w3'),
    ]

    error_text = 'Workshops shouldn`t overlap in time'
    assert not errors_if_overlapping(registrations, products, 'workshop', error_text)

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, product_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, product_key='w2'),
    ]
    assert error_text == errors_if_overlapping(registrations, products, 'workshop', error_text)

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, product_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, product_key='w3'),
        Registration(person=ms_y, registered_by=mr_x, product_key='w1'),
        Registration(person=ms_y, registered_by=mr_x, product_key='w3'),
        Registration(person=mr_x, registered_by=mr_x, product_key='p'),
    ]

    assert not errors_if_overlapping(registrations, products, 'workshop', error_text)

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, product_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, product_key='w2'),
        Registration(person=mr_x, registered_by=mr_x, product_key='w3'),
        Registration(person=ms_y, registered_by=mr_x, product_key='w1'),
        Registration(person=ms_y, registered_by=mr_x, product_key='w3'),
        Registration(person=mr_x, registered_by=mr_x, product_key='p'),
    ]

    assert error_text == errors_if_overlapping(registrations, products, 'workshop', error_text)
