from unittest.mock import Mock

import pytest
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE, ACCEPTED, WAITING
from salty_tickets.models.personal_info import PersonInfo
from salty_tickets.models.products import WorkshopProduct, ProductRegistration, WaitListedPartnerProduct, PartnerProduct
from salty_tickets.waiting_lists import RegistrationStats


def test_workshop_product():
    workshop_product = WorkshopProduct(name='Test Product')
    assert workshop_product.key == 'test_product'


def test_wait_listed_partner_product_get_available_quantity():
    workshop_product = WorkshopProduct(name='Test')
    assert workshop_product.max_available is None
    assert workshop_product.get_available_quantity() is None

    workshop_product = WaitListedPartnerProduct(name='Test', max_available=10)
    assert workshop_product.registrations == []
    assert workshop_product.get_available_quantity() == 10
    
    mr_one = PersonInfo(full_name="Mr One", email='mr.one@gmail.com')
    mr_two = PersonInfo(full_name="Mr Two", email='mr.two@gmail.com')


    registrations = [
        ProductRegistration(person=mr_one, status=ACCEPTED, dance_role=LEADER),
        ProductRegistration(person=mr_two, status=ACCEPTED, dance_role=LEADER),
    ]

    workshop_product = WaitListedPartnerProduct(name='Test', max_available=10, registrations=registrations)
    assert workshop_product.get_available_quantity() == 8

    registrations = [
        ProductRegistration(person=mr_one, status=ACCEPTED, dance_role=LEADER),
        ProductRegistration(person=mr_two, status=WAITING, dance_role=LEADER),
    ]

    workshop_product = WaitListedPartnerProduct(name='Test', max_available=10, registrations=registrations)
    assert workshop_product.get_available_quantity() == 9


def test_wait_listed_partner_product_waiting_list():
    mr_one = PersonInfo(full_name="Mr One", email='mr.one@gmail.com')
    mr_two = PersonInfo(full_name="Mr Two", email='mr.two@gmail.com')
    ms_one = PersonInfo(full_name="Ms One", email='ms.one@gmail.com')
    ms_two = PersonInfo(full_name="Ms Two", email='ms.two@gmail.com')
    ms_three = PersonInfo(full_name="Ms Three", email='ms.three@gmail.com')

    registrations = [
        ProductRegistration(person=mr_one, status=ACCEPTED, dance_role=LEADER),
        ProductRegistration(person=mr_two, status=ACCEPTED, dance_role=LEADER, as_couple=True, partner=ms_two),
        ProductRegistration(person=ms_one, status=ACCEPTED, dance_role=FOLLOWER),
        ProductRegistration(person=ms_two, status=ACCEPTED, dance_role=FOLLOWER, as_couple=True, partner=mr_two),
        ProductRegistration(person=ms_three, status=ACCEPTED, dance_role=FOLLOWER),
    ]

    workshop_product = WaitListedPartnerProduct(name='Test', max_available=10, registrations=registrations)
    assert workshop_product.waiting_list.registration_stats[LEADER] == RegistrationStats(accepted=2, waiting=0)
    assert workshop_product.waiting_list.registration_stats[FOLLOWER] == RegistrationStats(accepted=3, waiting=0)
    assert workshop_product.waiting_list.registration_stats[COUPLE] == RegistrationStats(accepted=2, waiting=0)

    #############
    registrations = [
        ProductRegistration(person=mr_one, status=ACCEPTED, dance_role=LEADER),
        ProductRegistration(person=mr_two, status=WAITING, dance_role=LEADER),
    ]

    workshop_product = WaitListedPartnerProduct(name='Test', max_available=10, registrations=registrations)
    assert workshop_product.waiting_list.registration_stats[LEADER] == RegistrationStats(accepted=1, waiting=1)

    ####
    workshop_product = WaitListedPartnerProduct(name='Test', max_available=10, ratio=1.5, registrations=registrations)
    assert workshop_product.waiting_list.ratio == 1.5
    assert workshop_product.waiting_list.max_available == 10


@pytest.mark.parametrize('value,result', [
    (LEADER, False),
    (FOLLOWER, False),
    ('', False),
    (None, False),
    (COUPLE, True),
])
def test_partner_product_needs_partner(value, result):
    """needs_partner is True only when COUPLE is selected"""
    product = PartnerProduct(name='Test Product')
    event_form = Mock()
    product_data = Mock()
    event_form.get_product_by_key.return_value = product_data

    product_data.add.data = value
    assert product.needs_partner(event_form) == result

