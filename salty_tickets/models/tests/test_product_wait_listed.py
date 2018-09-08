from dataclasses import dataclass
from salty_tickets.constants import ACCEPTED, LEADER, FOLLOWER, WAITING
from salty_tickets.models.products import WaitListedPartnerProduct
from salty_tickets.models.registrations import PersonInfo, ProductRegistration

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
    status: str = ACCEPTED
    active: bool = True


@dataclass
class CoupleRegistrationMeta:
    status: str = ACCEPTED
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
            person = PersonInfo(full_name=name, email=f'{name}@{dance_role}.com')
            reg = ProductRegistration(registered_by=person, person=person, dance_role=dance_role,
                                      status=meta.status, active=meta.active)
            registrations.append(reg)

        elif isinstance(meta, CoupleRegistrationMeta):
            name = LEADER_NAMES[leader_idx]
            leader_idx += 1
            leader = PersonInfo(full_name=name, email=f'{name}@leader.com')

            name = FOLLOWER_NAMES[follower_idx]
            follower_idx += 1
            follower = PersonInfo(full_name=name, email=f'{name}@follower.com')

            reg1 = ProductRegistration(registered_by=leader, person=leader, partner=follower,
                                       dance_role=LEADER, status=meta.status, active=meta.active)
            reg2 = ProductRegistration(registered_by=leader, person=follower, partner=leader,
                                       dance_role=FOLLOWER, status=meta.status, active=meta.active)
            registrations.append(reg1)
            registrations.append(reg2)

    return registrations


def assert_registrations_eq(list1, list2):
    assert sorted([r.person.email for r in list1]) == sorted([r.person.email for r in list2])


def test_wait_listed_partner_product_balance_no_waiting_list():
    product = WaitListedPartnerProduct(ratio=1.0, allow_first=1, name='Test', max_available=10)

    product.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        CoupleRegistrationMeta(),
        RegistrationMeta(FOLLOWER),
        RegistrationMeta(FOLLOWER),
    ])
    assert [] == product.balance_waiting_list()


def test_wait_listed_partner_product_balance_waiting_list():
    product = WaitListedPartnerProduct(ratio=1.0, allow_first=1, name='Test', max_available=10)

    product.registrations = util_generate_registrations([
        CoupleRegistrationMeta(WAITING),
        CoupleRegistrationMeta(WAITING),
        CoupleRegistrationMeta(WAITING),
    ])
    balanced = product.balance_waiting_list()
    assert_registrations_eq(product.registrations, balanced)
    assert all([r.status == ACCEPTED for r in product.registrations])


def test_wait_listed_partner_product_balance_waiting_list_can_accept_one():
    #### 2 leaders, 4 followers. can accept just 1 follower
    product = WaitListedPartnerProduct(ratio=1.5, allow_first=1, name='Test', max_available=10)
    product.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        CoupleRegistrationMeta(),
        RegistrationMeta(FOLLOWER, WAITING),
        RegistrationMeta(FOLLOWER, WAITING),
    ])
    balanced = product.balance_waiting_list()
    assert_registrations_eq([product.registrations[-2]], balanced)


def test_wait_listed_partner_product_balance_waiting_list_couple_first():
    product = WaitListedPartnerProduct(ratio=1.5, allow_first=1, name='Test', max_available=10)
    #### couple gets off the waiting list first
    product.ratio = 1.5
    product.allow_first = 1
    product.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        RegistrationMeta(FOLLOWER),
        RegistrationMeta(FOLLOWER, WAITING),
        CoupleRegistrationMeta(WAITING),
    ])
    balanced = product.balance_waiting_list()
    assert_registrations_eq(product.registrations[-2:], balanced)


def test_wait_listed_partner_product_balance_waiting_list_real_scenario():
    product = WaitListedPartnerProduct(ratio=1.5, allow_first=1, name='Test', max_available=10)
    #### couple gets off the waiting list first
    product.ratio = 1.5
    product.allow_first = 1
    product.registrations = util_generate_registrations([
        CoupleRegistrationMeta(),
        CoupleRegistrationMeta(),
        RegistrationMeta(FOLLOWER),
        RegistrationMeta(FOLLOWER, WAITING),
        RegistrationMeta(FOLLOWER, WAITING),
    ])
    # already 2 leads, 3 follows -> 1.5, 1 follower waiting
    assert [] == product.balance_waiting_list()

    # add 1 leader. Now 3 and 3. -> can add 1 more follower
    product.registrations += util_generate_registrations([RegistrationMeta(LEADER)])
    balanced = product.balance_waiting_list()
    assert_registrations_eq([product.registrations[5]], balanced)

    # add  1 couple. Now it is 4 and 5. Can add one more follower
    product.registrations += util_generate_registrations([CoupleRegistrationMeta()])
    balanced = product.balance_waiting_list()
    assert_registrations_eq([product.registrations[6]], balanced)
