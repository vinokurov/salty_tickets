from unittest.mock import Mock

import pytest
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE, ACCEPTED, WAITING
from salty_tickets.models.registrations import Person, Registration
from salty_tickets.models.tickets import WorkshopTicket, WaitListedPartnerTicket, PartnerTicket
from salty_tickets.waiting_lists import RegistrationStats


def test_workshop_ticket():
    workshop_ticket = WorkshopTicket(name='Test ticket')
    assert workshop_ticket.key == 'test_ticket'


def test_wait_listed_partner_ticket_get_available_quantity():
    workshop_ticket = WorkshopTicket(name='Test')
    assert workshop_ticket.max_available is None
    assert workshop_ticket.get_available_quantity() is None

    workshop_ticket = WaitListedPartnerTicket(name='Test', max_available=10)
    assert workshop_ticket.calculate_remaining([]) == 10
    
    mr_one = Person(full_name="Mr One", email='mr.one@gmail.com')
    mr_two = Person(full_name="Mr Two", email='mr.two@gmail.com')

    registrations = [
        Registration(person=mr_one, dance_role=LEADER, active=True),
        Registration(person=mr_two, dance_role=LEADER, active=True),
    ]

    workshop_ticket = WaitListedPartnerTicket(name='Test', max_available=10)
    assert workshop_ticket.calculate_remaining(registrations) == 8

    registrations = [
        Registration(person=mr_one, dance_role=LEADER, active=True),
        Registration(person=mr_two, wait_listed=True, dance_role=LEADER, active=True),
    ]

    workshop_ticket = WaitListedPartnerTicket(name='Test', max_available=10)
    assert workshop_ticket.calculate_remaining(registrations) == 9

    registrations = [
        Registration(person=mr_one, dance_role=LEADER, active=True),
        Registration(person=mr_two, dance_role=LEADER, active=False),
    ]

    workshop_ticket = WaitListedPartnerTicket(name='Test', max_available=10)
    assert workshop_ticket.calculate_remaining(registrations) == 9


def test_wait_listed_partner_ticket_waiting_list():
    mr_one = Person(full_name="Mr One", email='mr.one@gmail.com')
    mr_two = Person(full_name="Mr Two", email='mr.two@gmail.com')
    ms_one = Person(full_name="Ms One", email='ms.one@gmail.com')
    ms_two = Person(full_name="Ms Two", email='ms.two@gmail.com')
    ms_three = Person(full_name="Ms Three", email='ms.three@gmail.com')

    registrations = [
        Registration(person=mr_one, dance_role=LEADER, active=True),
        Registration(person=mr_two, dance_role=LEADER, partner=ms_two, active=True),
        Registration(person=ms_one, dance_role=FOLLOWER, active=True),
        Registration(person=ms_two, dance_role=FOLLOWER, partner=mr_two, active=True),
        Registration(person=ms_three, dance_role=FOLLOWER, active=False),
    ]

    workshop_ticket = WaitListedPartnerTicket(name='Test', max_available=10)
    workshop_ticket.numbers = workshop_ticket.calculate_ticket_numbers(registrations)
    assert workshop_ticket.waiting_list.registration_stats[LEADER] == RegistrationStats(accepted=2, waiting=0)
    assert workshop_ticket.waiting_list.registration_stats[FOLLOWER] == RegistrationStats(accepted=2, waiting=0)
    assert workshop_ticket.waiting_list.registration_stats[COUPLE] == RegistrationStats(accepted=2, waiting=0)

    #############
    registrations = [
        Registration(person=mr_one, dance_role=LEADER, active=True),
        Registration(person=mr_two, wait_listed=True, dance_role=LEADER, active=True),
    ]

    workshop_ticket = WaitListedPartnerTicket(name='Test', max_available=10)
    workshop_ticket.numbers = workshop_ticket.calculate_ticket_numbers(registrations)
    assert workshop_ticket.waiting_list.registration_stats[LEADER] == RegistrationStats(accepted=1, waiting=1)

    ####
    workshop_ticket = WaitListedPartnerTicket(name='Test', max_available=10, ratio=1.5)
    workshop_ticket.numbers = workshop_ticket.calculate_ticket_numbers(registrations)
    assert workshop_ticket.waiting_list.ratio == 1.5
    assert workshop_ticket.waiting_list.max_available == 10


@pytest.mark.parametrize('value,result', [
    (LEADER, False),
    (FOLLOWER, False),
    ('', False),
    (None, False),
    (COUPLE, True),
])
def test_partner_ticket_needs_partner(value, result):
    """needs_partner is True only when COUPLE is selected"""
    ticket = PartnerTicket(name='Test ticket')
    event_form = Mock()
    ticket_data = Mock()
    event_form.get_item_by_key.return_value = ticket_data

    ticket_data.add.data = value
    assert ticket.needs_partner(event_form) == result


