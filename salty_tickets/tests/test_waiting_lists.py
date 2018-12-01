from datetime import date

from salty_tickets.constants import LEADER, FOLLOWER, COUPLE
from salty_tickets.waiting_lists import SimpleWaitingList, RegistrationStats, BaseWaitingList, ProbabilityWaitingList, \
    waiting_probability, poisson_rate, waiting_probability_poisson


def test_simple_waiting_list():
    waiting_list = SimpleWaitingList(
        max_available=10,
        registration_stats={
            LEADER: RegistrationStats(accepted=2),
            FOLLOWER: RegistrationStats(accepted=3, waiting=1),
            COUPLE: RegistrationStats(accepted=2),
        },
        ratio=1.5
    )
    wl = waiting_list.waiting_stats
    assert wl[LEADER] is None
    assert wl[FOLLOWER] == 0.125 # chance to get accepted
    assert wl[COUPLE] is None
    assert waiting_list.allow_first == 10


def test_simple_waiting_list_can_add():
    waiting_list = SimpleWaitingList(max_available=10, ratio=1.5)
    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)


def test_simple_waiting_list__empty():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=0, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = SimpleWaitingList(max_available=10, ratio=1.5, allow_first=5, registration_stats=reg_stats_dict)

    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 0 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list
    assert {LEADER: None, FOLLOWER: None, COUPLE: None} == waiting_list.waiting_stats


def test_simple_waiting_list__not_reached_first_5_no_leads():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=2, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = SimpleWaitingList(max_available=10, ratio=1.5, allow_first=5, registration_stats=reg_stats_dict)

    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 2 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list
    assert {LEADER: None, FOLLOWER: None, COUPLE: None} == waiting_list.waiting_stats


def test_simple_waiting_list__just_reached_first_5_no_leads():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=5, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = SimpleWaitingList(max_available=10, ratio=1.5, allow_first=5, registration_stats=reg_stats_dict)

    assert waiting_list.can_add(LEADER)
    assert not waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 5 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list
    assert {LEADER: None, FOLLOWER: 0, COUPLE: None} == waiting_list.waiting_stats


def test_has_waiting_list():
    waiting_list = BaseWaitingList(
        max_available=10,
        registration_stats={
            LEADER: RegistrationStats(accepted=3),
            FOLLOWER: RegistrationStats(accepted=5, waiting=1),
            COUPLE: RegistrationStats(accepted=2),
        },
        ratio=1.5
    )
    assert waiting_list.has_waiting_list

    waiting_list.registration_stats[FOLLOWER].waiting = 0
    assert not waiting_list.has_waiting_list


def test_probability_waiting_list_formula():
    # almost no registrations
    assert 1 - waiting_probability(30, 1.4, 0, 0, 0.5) < 1e-4
    assert 1 - waiting_probability(30, 1.4, 2, 0, 0.5) < 1e-4

    # not violating ratio
    assert 1 == waiting_probability(30, 1.4, 13, 10, 0.5)

    # last place not violating ratio
    assert 1 == waiting_probability(30, 1.4, 15, 14, 0.5)

    # no places
    assert 0 == waiting_probability(30, 1.4, 15, 15, 0.5)

    # no way how ratio can be achieved
    assert 0 == waiting_probability(30, 1.4, 20, 5, 0.5)

    # this is less than other
    assert 1 == waiting_probability(30, 1.4, 0, 15, 0.5)
    assert 1 == waiting_probability(30, 1.4, 5, 15, 0.5)

    # some checks that make sense
    assert waiting_probability(30, 1.4, 5, 1, 0.4) > 0.95
    assert waiting_probability(30, 1.4, 11, 5, 0.4) < 0.95

    # monotonously decreases if this role increases
    p = waiting_probability(30, 1.4, 0, 5, 0.4)
    for i in range(1, 30):
        p1 = waiting_probability(30, 1.4, i, 5, 0.4)
        assert p1 <= p
        p = p1

    # monotonously increases if other role increases
    p = waiting_probability(30, 1.4, 10, 0, 0.4)
    for i in range(1, 20):
        p1 = waiting_probability(30, 1.4, 10, i, 0.4)
        assert p1 >= p
        p = p1


def test_probability_waiting_list():
    waiting_list = ProbabilityWaitingList(
        max_available=10,
        registration_stats={
            LEADER: RegistrationStats(accepted=3),
            FOLLOWER: RegistrationStats(accepted=5, waiting=1),
            COUPLE: RegistrationStats(accepted=2),
        },
        ratio=1.5
    )
    wl = waiting_list.waiting_stats
    assert wl[LEADER] is None
    assert wl[FOLLOWER] < 0.5
    assert wl[COUPLE] is None
    print(wl)


def test_probability_waiting_list_can_add():
    waiting_list = ProbabilityWaitingList(max_available=10, ratio=1.5)
    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)


def test_probability_waiting_list__empty():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=0, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = ProbabilityWaitingList(max_available=30, ratio=1.5,
                                          registration_stats=reg_stats_dict)

    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 0 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list
    assert [None, None, None] == list(waiting_list.waiting_stats.values())
    print(waiting_list.waiting_stats)


def test_probability_waiting_list__not_reached_first_5_no_leads():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=2, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = ProbabilityWaitingList(max_available=30, ratio=1.5,
                                          registration_stats=reg_stats_dict)

    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 2 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list

    print(waiting_list.waiting_stats)
    assert [None, None, None] == list(waiting_list.waiting_stats.values())


def test_probability_waiting_list__just_reached_first_5_no_leads():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=6, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = ProbabilityWaitingList(max_available=30, ratio=1.5,
                                          registration_stats=reg_stats_dict,
                                          expected_leads=10)

    assert waiting_list.can_add(LEADER)
    assert not waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 6 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list

    print(waiting_list.waiting_stats)
    assert waiting_list.waiting_stats[LEADER] is None
    assert waiting_list.waiting_stats[FOLLOWER] < 0.98


def test_probability_waiting_list__scenario1():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=3, waiting=0),
        FOLLOWER: RegistrationStats(accepted=6, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = ProbabilityWaitingList(max_available=30, ratio=1.4,
                                          registration_stats=reg_stats_dict,
                                          expected_leads=10)

    # first no waiting list
    assert waiting_list.can_add(FOLLOWER)

    # add one follower -> accepted
    waiting_list.registration_stats[FOLLOWER].accepted += 1
    assert not waiting_list.can_add(FOLLOWER)
    p1 = waiting_list.probability_for_option(FOLLOWER)

    # add follower -> waiting list
    waiting_list.registration_stats[FOLLOWER].waiting += 1
    assert not waiting_list.can_add(FOLLOWER)
    p2 = waiting_list.probability_for_option(FOLLOWER)
    assert p2 < p1

    # add follower -> to accepted (e.g. signed up with ptn_token)
    waiting_list.registration_stats[FOLLOWER].accepted += 1
    assert not waiting_list.can_add(FOLLOWER)
    p3 = waiting_list.probability_for_option(FOLLOWER)
    assert p3 < p2

    # now add leader
    waiting_list.registration_stats[LEADER].accepted += 1
    assert not waiting_list.can_add(FOLLOWER)
    p4 = waiting_list.probability_for_option(FOLLOWER)
    assert p4 > p3


def test_poisson_rate():
    assert 10 == poisson_rate(date(2018, 1, 1), date(2018, 1, 31), date(2018, 1, 1), 10)
    assert 5 == poisson_rate(date(2018, 1, 1), date(2018, 1, 30), date(2018, 1, 16), 10)
    assert 1/3.0 == poisson_rate(date(2018, 1, 1), date(2018, 1, 30), date(2018, 1, 30), 10)


def test_waiting_probability_poisson():
    # almost no registrations
    assert 1 - waiting_probability_poisson(30, 1.4, 0, 0, 10) < 1e-2
    assert 1 - waiting_probability_poisson(30, 1.4, 2, 0, 10) < 1e-2

    # not violating ratio
    assert 1 == waiting_probability_poisson(30, 1.4, 13, 10, 10)

    # last place not violating ratio
    assert 1 == waiting_probability_poisson(30, 1.4, 15, 14, 10)

    # no places
    assert 0 == waiting_probability_poisson(30, 1.4, 15, 15, 10)

    # no way how ratio can be achieved
    assert 0 == waiting_probability_poisson(30, 1.4, 20, 5, 10)

    # this is less than other
    assert 1 == waiting_probability_poisson(30, 1.4, 0, 15, 10)
    assert 1 == waiting_probability_poisson(30, 1.4, 5, 15, 10)

    # some checks that make sense
    assert waiting_probability_poisson(30, 1.4, 5, 1, 10) > 0.95
    assert waiting_probability_poisson(30, 1.4, 11, 5, 5) < 0.95

    # monotonously decreases if this role increases
    p = waiting_probability_poisson(30, 1.4, 0, 5, 10)
    for i in range(1, 30):
        p1 = waiting_probability_poisson(30, 1.4, i, 5, 10)
        assert p1 <= p
        p = p1
        print(p)

    # monotonously increases if other role increases
    p = waiting_probability_poisson(30, 1.4, 10, 0, 10)
    for i in range(1, 20):
        p1 = waiting_probability_poisson(30, 1.4, 10, i, 10)
        assert p1 >= p
        p = p1

    # monotonously decreases as rate decreases
    p = waiting_probability_poisson(30, 1.4, 11, 5, 10)
    for i in range(1, 10):
        p1 = waiting_probability_poisson(30, 1.4, 11, 5, 10-i)
        assert p1 <= p
        p = p1
