import pytest
from salty_tickets.models.registrations import Person, Registration
from salty_tickets.models.tickets import Ticket, WorkshopTicket, PartyTicket, FestivalPassTicket
from salty_tickets.pricers import TicketPricer, SpecialPriceIfMoreThanPriceRule, CombinationsPriceRule, BasePriceRule, \
    MindTheShagPriceRule, TaggedBasePriceRule


def test_base_pricer():
    ticket_list = [
        Ticket(name='ticket 1', base_price=10),
        Ticket(name='ticket 2', base_price=20),
        Ticket(name='ticket 3', base_price=30),
    ]

    event_tickets = {p.key: p for p in ticket_list}
    pricer = TicketPricer(event_tickets)

    registrations = [
        Registration(ticket_key=ticket_list[0].key),
        Registration(ticket_key=ticket_list[2].key),
    ]

    for r in registrations:
        assert r.price is None

    pricer.price_all(registrations)
    assert registrations[0].price == ticket_list[0].base_price
    assert registrations[1].price == ticket_list[2].base_price


def test_pricer_special_price_if_more_than():
    tickets = [
        Ticket(name='ticket 1', base_price=25, tags={'workshop'}),
        Ticket(name='ticket 2', base_price=25, tags={'workshop'}),
        Ticket(name='ticket 3', base_price=25, tags={'workshop'}),
        Ticket(name='ticket 4', base_price=15, tags={'regular'}),
    ]

    event_tickets = {p.key: p for p in tickets}
    pricing_rules = [
        SpecialPriceIfMoreThanPriceRule(more_than=2, tag='workshop', special_price=20),
        BasePriceRule(),
    ]
    pricer = TicketPricer(event_tickets, pricing_rules)

    registrations = [Registration(ticket_key=p.key) for p in tickets]

    pricer.price_all(registrations)
    assert [25, 25, 20, 15] == [r.price for r in registrations]


def test_pricer_special_price_if_more_than_2_persons():
    tickets = [
        Ticket(name='ticket 1', base_price=25, tags={'workshop'}),
        Ticket(name='ticket 2', base_price=25, tags={'workshop'}),
        Ticket(name='ticket 3', base_price=25, tags={'workshop'}),
        Ticket(name='ticket 4', base_price=15, tags={'regular'}),
    ]

    event_tickets = {p.key: p for p in tickets}
    pricing_rules = [
        SpecialPriceIfMoreThanPriceRule(more_than=2, tag='workshop', special_price=20),
        BasePriceRule(),
    ]
    pricer = TicketPricer(event_tickets, pricing_rules)

    mr_one = Person(full_name='Mr One', email='Mr.One@one.com')
    ms_two = Person(full_name='Ms Two', email='Ms.Two@two.com')

    registrations = [
        Registration(ticket_key=tickets[0].key, person=mr_one),
        Registration(ticket_key=tickets[0].key, person=ms_two),

        Registration(ticket_key=tickets[1].key, person=mr_one),
        Registration(ticket_key=tickets[1].key, person=ms_two),

        Registration(ticket_key=tickets[2].key, person=ms_two),

        Registration(ticket_key=tickets[3].key, person=mr_one),
    ]

    pricer.price_all(registrations)
    assert [r.price for r in registrations] == [25, 25, 25, 25, 20, 15]


def test_combinations_price_rule():
    tickets = [
        Ticket(name='w1', base_price=25, tags={'workshop'}),
        Ticket(name='w2', base_price=25, tags={'workshop'}),
        Ticket(name='w3', base_price=25, tags={'workshop'}),
        Ticket(name='p1', base_price=15, tags={'party'}),
        Ticket(name='p2', base_price=15, tags={'party'}),
    ]

    event_tickets = {p.key: p for p in tickets}
    pricing_rules = [
        CombinationsPriceRule(tag='workshop', count_prices={'2': 40, '3': 57}),
    ]
    pricer = TicketPricer(event_tickets, pricing_rules)

    mr_x = Person(full_name='Mr.X', email='mr.x@x.com')
    ms_y = Person(full_name='Ms.Y', email='ms.y@y.com')

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w2'),
    ]
    pricer.price_all(registrations)
    assert [20.0, 20.0] == [r.price for r in registrations]

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w2'),
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w3'),
    ]
    pricer.price_all(registrations)
    assert [19, 19, 19] == [r.price for r in registrations]

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w2'),
        Registration(person=ms_y, registered_by=mr_x, ticket_key='w1'),
    ]
    pricer.price_all(registrations)
    assert [20, 20, None] == [r.price for r in registrations]

    registrations = [
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w1'),
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w2'),
        Registration(person=mr_x, registered_by=mr_x, ticket_key='w3'),
        Registration(person=ms_y, registered_by=mr_x, ticket_key='w1'),
        Registration(person=ms_y, registered_by=mr_x, ticket_key='w2'),
    ]
    pricer.price_all(registrations)
    assert [19, 19, 19, 20, 20] == [r.price for r in registrations]


@pytest.fixture
def mts_tickets():
    tickets = [
        WorkshopTicket(name='w1', base_price=35.0, tags={'station'}),
        WorkshopTicket(name='w2', base_price=35.0, tags={'station'}),
        WorkshopTicket(name='w3', base_price=35.0, tags={'station'}),
        WorkshopTicket(name='w4', base_price=35.0, tags={'station'}),
        WorkshopTicket(name='w5', base_price=35.0, tags={'station'}),
        WorkshopTicket(name='w6', base_price=35.0, tags={'station'}),
        WorkshopTicket(name='beg1', base_price=35.0, tags={'station', 'train'}),
        WorkshopTicket(name='beg2', base_price=35.0, tags={'station', 'train'}),
        WorkshopTicket(name='clinic', base_price=40.0, tags={'station', 'clinic'}),
        PartyTicket(name='p1', base_price=20.0, tags={'party'}),
        PartyTicket(name='p2', base_price=30.0, tags={'party'}),
        PartyTicket(name='p3', base_price=15.0, tags={'party'}),
        FestivalPassTicket(name='full_pass', base_price=120.0, tags={'pass', 'includes_parties', 'station_discount_3', 'includes_parties'}),
        FestivalPassTicket(name='shag_novice', base_price=90.0, tags={'pass', 'includes_parties', 'station_discount_2', 'includes_parties'}),
        FestivalPassTicket(name='shag_novice_no_parties', base_price=45.0, tags={'pass', 'station_discount_2'}),
        FestivalPassTicket(name='party_pass', base_price=55.0, tags={'pass', 'includes_parties', 'includes_parties'}),
    ]
    return {p.key: p for p in tickets}


@pytest.fixture
def mts_pricing_rules():
    return [
        MindTheShagPriceRule(price_station=30.0, price_station_extra=25.0, price_clinic=40.0,
                             price_cheaper_station_extra=15.0),
        TaggedBasePriceRule(tag='pass'),
        TaggedBasePriceRule(tag='party'),
    ]


@pytest.fixture
def mr_x():
    return Person(full_name='Mr.X', email='mr.x@x.com')


@pytest.fixture
def ms_y():
    return Person(full_name='Ms.Y', email='ms.y@y.com')


@pytest.mark.parametrize("registration_keys,expected_prices", [
    ("w1 w2", [35, 35]),
    ("p1 p2", [20, 30]),
    ("p3 beg1", [15, 35]),
    ("w1 w2 p3", [35, 35, 15]),
    ("w1 clinic p3", [35, 40, 15]),

    ('w1 w2 w3 p1 p2 p3 full_pass', [0, 0, 0, 0, 0, 0, 120]),

    ('beg1 beg2 p1 p2 p3 shag_novice', [0, 0, 0, 0, 0, 90]),
    ('beg1 beg2 shag_novice_no_parties', [0, 0, 45]),
    ('beg1 beg2 p1 p2 shag_novice_no_parties', [0, 0, 20, 30, 45]),

    ('p1 p2 p3 party_pass', [0, 0, 0, 55]),
    ('w1 p1 p2 p3 party_pass', [35, 0, 0, 0, 55]),

    ('w1 w2 w3 w4 p1 p2 p3 full_pass', [0, 0, 0, 25, 0, 0, 0, 120]),

    ('w1 w2 w3 w4 w5 p1 p2 p3 full_pass', [0, 0, 0, 25, 25, 0, 0, 0, 120]),

    ('w1 beg1 beg2 p1 p2 p3 shag_novice', [25, 0, 0, 0, 0, 0, 90]),
    ('w1 beg1 beg2 p2 p3 shag_novice_no_parties', [25, 0, 0, 30, 15, 45]),

    ('w1 beg1 beg2 w2 p1 p2 p3 shag_novice', [25, 0, 0, 25, 0, 0, 0, 90]),
    ('w1 beg1 beg2 w2 p2 p3 shag_novice_no_parties', [25, 0, 0, 25, 30, 15, 45]),

    ('w1 w2 clinic p1 p2 p3 full_pass', [0, 0, 15, 0, 0, 0, 120]),

    ('w1 w2 clinic w3 p1 p2 p3 full_pass', [0, 0, 15, 25, 0, 0, 0, 120]),
    ('w1 w2 w3 clinic p1 p2 p3 full_pass', [0, 0, 0, 40, 0, 0, 0, 120]),
    ('w1 w2 w3 w4 clinic p1 p2 p3 full_pass', [0, 0, 0, 25, 40, 0, 0, 0, 120]),

    ('w1 beg1 beg2 clinic p1 p2 p3 shag_novice', [25, 0, 0, 40, 0, 0, 0, 90]),
])
def test_mind_the_shag_price_rule(mts_tickets, mts_pricing_rules, mr_x, ms_y, registration_keys, expected_prices):
    pricer = TicketPricer(mts_tickets, mts_pricing_rules)

    # solo registration
    registrations = [Registration(person=mr_x, registered_by=mr_x, ticket_key=k)
                     for k in registration_keys.split(' ')]
    pricer.price_all(registrations)
    assert sum(expected_prices) == sum([r.price for r in registrations])
    assert expected_prices == [r.price for r in registrations]

    # couple registration
    registrations_x = [Registration(person=mr_x, registered_by=mr_x, ticket_key=k)
                       for k in registration_keys.split(' ')]
    registrations_y = [Registration(person=ms_y, registered_by=mr_x, ticket_key=k)
                       for k in registration_keys.split(' ')]
    registrations_couple = registrations_x + registrations_y
    pricer.price_all(registrations_couple)
    expected_prices_couple = expected_prices + expected_prices
    assert sum(expected_prices_couple) == sum([r.price for r in registrations_couple])
    assert expected_prices_couple == [r.price for r in registrations_couple]

    # partner has just one workshop
    registrations_couple = registrations_x + [Registration(person=ms_y, registered_by=mr_x, ticket_key='w1')]
    pricer.price_all(registrations_couple)
    expected_prices_couple = expected_prices + [35]
    assert sum(expected_prices_couple) == sum([r.price for r in registrations_couple])
    assert expected_prices_couple == [r.price for r in registrations_couple]


@pytest.mark.parametrize("prior_registration_keys,registration_keys,expected_prices", [
    ("w1 w2", "w3", [35]),
    ("w1 w2", "party_pass", [55]),
    ("w1 w2 p1", "party_pass", [35]),  # party is 20, hence party_pass upgrade is 55-20=35
    ("w1 w2", "full_pass", [50]),  # full_pass=120, station=30, upgrade=120-2*30=60
    ("w1 w2 p1", "full_pass", [30]),  # full_pass=120, station=35, upgrade=120-2*35-20=30
    ("p1 p2 p3 party_pass", "full_pass", [65]),  # full_pass=120, party_pass=55
    ("w1 p1 p2 p3 party_pass", "full_pass", [30]),  # full_pass=120, party_pass=55
    ("w1 w2 p1 p2 p3 party_pass", "full_pass", [-5]),  # full_pass=120, party_pass=55
    ("w1", "shag_novice_no_parties", [35]),  # shag_novice_no_parties=45
    ("w1 p1", "shag_novice", [60]),  # shag_novice=90. 90-5-20=65
    ("beg1", "shag_novice_no_parties", [10]),  # shag_novice_no_parties=45, beg1=30
    ("beg1 p1", "shag_novice", [35]),  # 90 - 35 - 20 = 35
])
def test_mind_the_shag_price_rule_with_prior(mts_tickets, mts_pricing_rules, mr_x, ms_y,
                                             prior_registration_keys, registration_keys, expected_prices):
    pricer = TicketPricer(mts_tickets, mts_pricing_rules)

    # solo registration
    prior_registrations = [Registration(person=mr_x, registered_by=mr_x, ticket_key=k, active=True)
                     for k in prior_registration_keys.split(' ')]
    registrations = [Registration(person=mr_x, registered_by=mr_x, ticket_key=k)
                     for k in registration_keys.split(' ')]
    pricer.price_all(registrations, prior_registrations=prior_registrations)
    assert sum(expected_prices) == sum([r.price for r in registrations])
    assert expected_prices == [r.price for r in registrations]

    # couple registration
    prior_registrations_x = [Registration(person=mr_x, registered_by=mr_x, ticket_key=k, active=True)
                       for k in prior_registration_keys.split(' ')]
    prior_registrations_y = [Registration(person=ms_y, registered_by=mr_x, ticket_key=k, active=True)
                       for k in prior_registration_keys.split(' ')]
    prior_registrations_couple = prior_registrations_x + prior_registrations_y
    registrations_x = [Registration(person=mr_x, registered_by=mr_x, ticket_key=k)
                       for k in registration_keys.split(' ')]
    registrations_y = [Registration(person=ms_y, registered_by=mr_x, ticket_key=k)
                       for k in registration_keys.split(' ')]
    registrations_couple = registrations_x + registrations_y
    pricer.price_all(registrations_couple, prior_registrations=prior_registrations_couple)
    expected_prices_couple = expected_prices + expected_prices
    assert sum(expected_prices_couple) == sum([r.price for r in registrations_couple])
    assert expected_prices_couple == [r.price for r in registrations_couple]

    # prior was couple, now solo
    pricer.price_all(registrations_x, prior_registrations=prior_registrations_couple)
    assert sum(expected_prices) == sum([r.price for r in registrations_x])
    assert expected_prices == [r.price for r in registrations_x]
