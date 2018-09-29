from salty_tickets.constants import LEADER, FOLLOWER, COUPLE
from salty_tickets.waiting_lists import AutoBalanceWaitingList, RegistrationStats


def test_auto_balance_waiting_list():
    waiting_list = AutoBalanceWaitingList(
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
    assert wl[FOLLOWER] == 1
    assert wl[COUPLE] is None
    assert waiting_list.allow_first == 10


def test_waiting_list_can_add():
    waiting_list = AutoBalanceWaitingList(max_available=10, ratio=1.5)
    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)


def test_waiting_list__empty():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=0, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = AutoBalanceWaitingList(max_available=10, ratio=1.5, allow_first=5, registration_stats=reg_stats_dict)

    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 0 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list
    assert {LEADER: None, FOLLOWER: None, COUPLE: None} == waiting_list.waiting_stats


def test_waiting_list__not_reached_first_5_no_leads():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=2, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = AutoBalanceWaitingList(max_available=10, ratio=1.5, allow_first=5, registration_stats=reg_stats_dict)

    assert waiting_list.can_add(LEADER)
    assert waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 2 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list
    assert {LEADER: None, FOLLOWER: None, COUPLE: None} == waiting_list.waiting_stats


def test_waiting_list__just_reached_first_5_no_leads():
    reg_stats_dict = {
        LEADER: RegistrationStats(accepted=0, waiting=0),
        FOLLOWER: RegistrationStats(accepted=5, waiting=0),
        COUPLE: RegistrationStats(accepted=0, waiting=0)
    }
    waiting_list = AutoBalanceWaitingList(max_available=10, ratio=1.5, allow_first=5, registration_stats=reg_stats_dict)

    assert waiting_list.can_add(LEADER)
    assert not waiting_list.can_add(FOLLOWER)
    assert waiting_list.can_add(COUPLE)

    assert 5 == waiting_list.total_accepted
    assert not waiting_list.needs_balancing()
    assert waiting_list.current_ratio is None
    assert not waiting_list.has_waiting_list
    assert {LEADER: None, FOLLOWER: 0, COUPLE: None} == waiting_list.waiting_stats


def test_has_waiting_list():
    waiting_list = AutoBalanceWaitingList(
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
