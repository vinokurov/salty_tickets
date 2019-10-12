from flask import Flask as _Flask
import pytest
from dataclasses import dataclass
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE
from salty_tickets.forms import create_event_form
from salty_tickets.models.event import Event
from salty_tickets.models.tickets import WaitListedPartnerTicket
from salty_tickets.models.registrations import Person, Registration
from salty_tickets.tokens import PartnerToken

LEADER_NAMES = [
    'Dallas',
    'Rueben',
    'Sydney',
    'Gail',
    'Lonnie',
    'Santos',
    'Colton',
    'Donovan',
    'Dominick',
    'Brock',
    'Isreal',
    'Geraldo',
    'Agustin',
    'Merrill',
    'Bobby',
    'Bradly',
    'Franklin',
    'Aldo',
    'Wesley',
    'Dylan',
    'Eusebio',
    'Dean',
    'Hyman',
    'Wilford',
    'Jerold',
    'Toby',
    'Mohammad',
    'Maria',
    'Donny',
    'Mitchell',
]
FOLLOWER_NAMES = [
    'Cassidy',
    'Kamilah',
    'Leonida',
    'Pandora',
    'Willa',
    'Judi',
    'Chloe',
    'Jaleesa',
    'Ilse',
    'Arielle',
    'Deena',
    'Vonda',
    'Nichole',
    'Kena',
    'Laquanda',
    'Yvonne',
    'Shara',
    'Loretta',
    'Oliva',
    'Lourdes',
    'Tula',
    'Laurice',
    'Tresa',
    'Cicely',
    'Arlena',
    'Patty',
    'Tyra',
    'Ena',
    'Kenisha',
    'Cira',
]


@dataclass
class RegistrationMeta:
    dance_role: str
    wait_listed: bool = False
    active: bool = True


@dataclass
class CoupleRegistrationMeta:
    wait_listed: bool = False
    active: bool = True


def util_generate_registrations(meta_list):
    registrations = []
    leader_idx = 0
    follower_idx = 0
    for meta in meta_list:
        if isinstance(meta, RegistrationMeta):
            dance_role = meta.dance_role
            if dance_role == LEADER:
                name = LEADER_NAMES[leader_idx]
                leader_idx += 1
            else:
                name = FOLLOWER_NAMES[follower_idx]
                follower_idx += 1
            person = Person(full_name=name, email=f'{name}@{dance_role}.com')
            reg = Registration(registered_by=person, person=person, dance_role=dance_role,
                               wait_listed=meta.wait_listed, active=meta.active)
            registrations.append(reg)

        elif isinstance(meta, CoupleRegistrationMeta):
            name = LEADER_NAMES[leader_idx]
            leader_idx += 1
            leader = Person(full_name=name, email=f'{name}@leader.com')

            name = FOLLOWER_NAMES[follower_idx]
            follower_idx += 1
            follower = Person(full_name=name, email=f'{name}@follower.com')

            reg1 = Registration(registered_by=leader, person=leader, partner=follower,
                                dance_role=LEADER, wait_listed=meta.wait_listed, active=meta.active)
            reg2 = Registration(registered_by=leader, person=follower, partner=leader,
                                dance_role=FOLLOWER, wait_listed=meta.wait_listed, active=meta.active)
            registrations.append(reg1)
            registrations.append(reg2)

    return registrations


def assert_registrations_eq(list1, list2):
    assert sorted([r.person.email for r in list1]) == sorted([r.person.email for r in list2])


def test_wait_listed_partner_ticket_balance_no_waiting_list():
    ticket = WaitListedPartnerTicket(ratio=1.0, allow_first=1, name='Test', max_available=10)

    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        CoupleRegistrationMeta(),
        RegistrationMeta(FOLLOWER),
        RegistrationMeta(FOLLOWER),
    ])
    assert [] == ticket.balance_waiting_list()


def test_wait_listed_partner_ticket_balance_waiting_list():
    ticket = WaitListedPartnerTicket(ratio=1.0, allow_first=1, name='Test', max_available=10)

    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(wait_listed=True),
        CoupleRegistrationMeta(wait_listed=True),
        CoupleRegistrationMeta(wait_listed=True),
    ])
    balanced = ticket.balance_waiting_list()
    assert_registrations_eq(ticket.registrations, balanced)
    assert not any([r.wait_listed for r in ticket.registrations])


def test_wait_listed_partner_ticket_balance_waiting_list_can_accept_one():
    #### 2 leaders, 4 followers. can accept just 1 follower
    ticket = WaitListedPartnerTicket(ratio=1.5, allow_first=1, name='Test', max_available=10)
    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        CoupleRegistrationMeta(),
        RegistrationMeta(FOLLOWER, wait_listed=True),
        RegistrationMeta(FOLLOWER, wait_listed=True),
    ])
    balanced = ticket.balance_waiting_list()
    assert_registrations_eq([ticket.registrations[-2]], balanced)


def test_wait_listed_partner_ticket_balance_waiting_list_couple_first():
    ticket = WaitListedPartnerTicket(ratio=1.5, allow_first=1, name='Test', max_available=10)
    #### couple gets off the waiting list first
    ticket.ratio = 1.5
    ticket.allow_first = 1
    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        RegistrationMeta(FOLLOWER),
        RegistrationMeta(FOLLOWER, wait_listed=True),
        CoupleRegistrationMeta(wait_listed=True),
    ])
    balanced = ticket.balance_waiting_list()
    assert_registrations_eq(ticket.registrations[-2:], balanced)


def test_wait_listed_partner_ticket_balance_waiting_list_real_scenario():
    ticket = WaitListedPartnerTicket(ratio=1.5, allow_first=1, name='Test', max_available=10)
    #### couple gets off the waiting list first
    ticket.ratio = 1.5
    ticket.allow_first = 1
    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        CoupleRegistrationMeta(),
        RegistrationMeta(FOLLOWER),
        RegistrationMeta(FOLLOWER, wait_listed=True),
        RegistrationMeta(FOLLOWER, wait_listed=True),
    ])
    # already 2 leads, 3 follows -> 1.5, 1 follower waiting
    assert [] == ticket.balance_waiting_list()

    # add 1 leader. Now 3 and 3. -> can add 1 more follower
    ticket.registrations += util_generate_registrations([RegistrationMeta(LEADER)])
    balanced = ticket.balance_waiting_list()
    assert_registrations_eq([ticket.registrations[5]], balanced)

    # add  1 couple. Now it is 4 and 5. Can add one more follower
    ticket.registrations += util_generate_registrations([CoupleRegistrationMeta()])
    balanced = ticket.balance_waiting_list()
    assert_registrations_eq([ticket.registrations[6]], balanced)


class Flask(_Flask):
    testing = True
    secret_key = __name__

    def make_response(self, rv):
        if rv is None:
            rv = ''

        return super(Flask, self).make_response(rv)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def test_wait_listed_parse_form(app):
    ticket = WaitListedPartnerTicket(ratio=1.5, allow_first=1, name='Test', max_available=10)
    ticket.ratio = 1.5
    ticket.allow_first = 1
    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),   # 1/1 = 1
        CoupleRegistrationMeta(),   # 2/2 = 1
        RegistrationMeta(FOLLOWER),  # 3/2 = 1.5
    ])
    event = Event(name='Test Event', tickets={'test': ticket})

    # will accept leader
    with app.app_context():
        form = create_event_form(event)()
    form.get_item_by_key('test').add.data = LEADER
    regs = ticket.parse_form(form)
    assert not regs[0].wait_listed

    # follower will be wait listed
    form.get_item_by_key('test').add.data = FOLLOWER
    regs = ticket.parse_form(form)
    assert regs[0].wait_listed

    # will accept couple event if there's waiting list for followers
    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),   # 1/1 = 1
        CoupleRegistrationMeta(),   # 2/2 = 1
        RegistrationMeta(FOLLOWER),  # 3/2 = 1.5
        RegistrationMeta(FOLLOWER),  # 4/2 = 2.0
    ])
    form.get_item_by_key('test').add.data = COUPLE
    regs = ticket.parse_form(form)
    assert not any([r.wait_listed for r in regs])

    # now that we have a couple in a waiting list -> will put a new couple in the wait list
    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),   # 1/1 = 1
        CoupleRegistrationMeta(wait_listed=True),
    ])
    assert not ticket.waiting_list.can_add(COUPLE)
    regs = ticket.parse_form(form)
    assert all([r.wait_listed for r in regs])


def test_wait_listed_apply_extra_partner(app):
    ticket = WaitListedPartnerTicket(ratio=1.5, allow_first=1, name='Test', max_available=10)

    me = Person('Mr X', 'mr.x@xx.com')
    another_one = Person('Mr Z', 'mr.z@zz.com')

    names = FOLLOWER_NAMES.copy()

    def pop_person():
        _name = names.pop()
        return Person(_name, _name.replace(' ', '.') + '@yy.com')

    # none of the extra registrations is available for me
    my_registration = Registration(person=me, wait_listed=True, active=True, dance_role=LEADER, ticket_key='test')
    extra_registrations = [
        Registration(person=pop_person(), wait_listed=False, active=True, dance_role=FOLLOWER, ticket_key='another'),
        Registration(person=pop_person(), wait_listed=False, active=True, dance_role=LEADER, ticket_key='test'),
        Registration(person=pop_person(), partner=another_one, wait_listed=False, active=True, dance_role=FOLLOWER, ticket_key='test'),
        Registration(person=pop_person(), wait_listed=False, active=False, dance_role=FOLLOWER, ticket_key='test'),
    ]
    regs = ticket.apply_extra_partner(my_registration, extra_registrations)
    assert not regs
    assert my_registration.wait_listed

    # I am wait listed, partner is wait listed, we both get off the wait list
    my_registration = Registration(person=me, wait_listed=True, active=True, dance_role=LEADER, ticket_key='test')
    extra_registrations = [
        Registration(person=pop_person(), wait_listed=False, active=True, dance_role=FOLLOWER, ticket_key='another'),
        Registration(person=pop_person(), wait_listed=True, active=True, dance_role=FOLLOWER, ticket_key='test'),
        Registration(person=pop_person(), wait_listed=False, active=True, dance_role=FOLLOWER, ticket_key='test'),
    ]
    applied_reg = ticket.apply_extra_partner(my_registration, extra_registrations)
    assert extra_registrations[1] == applied_reg
    assert not applied_reg.wait_listed
    assert me == applied_reg.partner
    assert applied_reg.person == my_registration.partner
    assert not my_registration.wait_listed

    # too many people, can't add couple
    ticket = WaitListedPartnerTicket(ratio=1.5, allow_first=1, name='Test', max_available=5)
    ticket.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        CoupleRegistrationMeta(wait_listed=True),
    ])
    assert not ticket.waiting_list.can_add(COUPLE)

    my_registration = Registration(person=me, wait_listed=True, active=True, dance_role=LEADER, ticket_key='test')
    extra_registrations = [
        Registration(person=pop_person(), wait_listed=True, active=True, dance_role=FOLLOWER, ticket_key='test'),
    ]
    applied_reg = ticket.apply_extra_partner(my_registration, extra_registrations)
    assert not applied_reg
    assert my_registration.wait_listed
