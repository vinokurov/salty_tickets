from waiting_lists import AutoBalanceWaitingList, RegistrationStats


def test_auto_balance_waiting_list():
    waiting_list = AutoBalanceWaitingList(
        max_available=10,
        registration_stats={
            'leader': RegistrationStats(accepted=3),
            'follower': RegistrationStats(accepted=5, waiting=1),
            'couple': RegistrationStats(accepted=2),
        },
        ratio=1.5
    )
    wl = waiting_list.waiting_stats
    assert wl['leader'] is None
    assert wl['follower'] == 1
    assert wl['couple'] is None
