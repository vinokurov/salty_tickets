import math
from datetime import date
from typing import Dict, Optional

from dataclasses import dataclass, field
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE
from scipy.stats import binom, poisson


@dataclass
class RegistrationStats:
    accepted: int = 0
    waiting: int = 0

    @property
    def total(self):
        return self.accepted + self.waiting


def flip_role(role):
    if role:
        return {
            LEADER: FOLLOWER,
            FOLLOWER: LEADER,
        }[role]


def waiting_probability(max_available, ratio, this, other, p_other):
    if this + other >= max_available:
        return 0

    if other and (this + 1) / other <= ratio:
        return 1

    k = math.ceil(this / ratio) - other
    n = max_available - this - other
    p = 1 - binom.cdf(k, n, p_other)
    return p


def poisson_rate(start_date: date, end_date: date, today: date, expected: int) -> float:
    total_days = (end_date - start_date).days + 1
    remaining_days = (end_date - today).days + 1
    return expected / total_days * remaining_days


def waiting_probability_poisson(max_available, ratio, this, other, rate):
    if this + other >= max_available:
        return 0

    if other and (this + 1) / other <= ratio:
        return 1

    if this > other and this + this / ratio > max_available:
        return 0

    k = math.ceil(this / ratio) - other
    p = 1 - poisson.cdf(k, mu=rate)
    return p


@dataclass
class BaseWaitingList:
    """
    Base class for waiting lists.
    Need to override methods: can_add() and waiting_list_for_option()
    """
    max_available: int
    ratio: float
    registration_stats: Dict[str, RegistrationStats] = field(default_factory=dict)
    expected_leads: int = None
    expected_follows: int = None

    def __post_init__(self):
        for o in [LEADER, FOLLOWER, COUPLE]:
            if o not in self.registration_stats:
                self.registration_stats[o] = RegistrationStats()

        if self.expected_leads is None:
            self.expected_leads = int(self.max_available/2)

        if self.expected_follows is None:
            self.expected_follows = int(self.max_available/2)

        self._p = {
            LEADER: self.expected_leads / self.max_available,
            FOLLOWER: self.expected_follows / self.max_available
        }

    @property
    def waiting_stats(self) -> dict:
        return {o: self.waiting_list_for_option(o) for o in [LEADER, FOLLOWER, COUPLE]}

    @property
    def has_waiting_list(self) -> bool:
        stats = self.registration_stats
        return stats[LEADER].waiting > 0 or stats[FOLLOWER].waiting > 0

    @property
    def current_ratio(self):
        round_digits = 3
        try:
            ratio = max(self.registration_stats[LEADER].accepted / self.registration_stats[FOLLOWER].accepted,
                        self.registration_stats[FOLLOWER].accepted / self.registration_stats[LEADER].accepted)
            return round(ratio, round_digits)
        except ZeroDivisionError:
            return None

    @property
    def total_accepted(self):
        return self.registration_stats[LEADER].accepted + self.registration_stats[FOLLOWER].accepted

    def needs_balancing(self, option: str = None) -> bool:
        if option is None:
            return any([self.needs_balancing(o) for o in [LEADER, FOLLOWER, COUPLE]])
        else:
            return self.can_add(option, consider_waiting_list=False) \
                   and self.registration_stats[option].waiting > 0

    def probability_for_option(self, option) -> float:
        if option == COUPLE:
            if self.total_accepted + 2 <= self.max_available:
                return 1
            else:
                return 0

        other_role = flip_role(option)
        this_role_accepted = self.registration_stats[option].accepted
        this_role_waiting = self.registration_stats[option].waiting
        other_role_accepted = self.registration_stats[other_role].accepted
        total_accepted = self.total_accepted

        if total_accepted + 1 > self.max_available:
            return False

        return waiting_probability(
            self.max_available,
            self.ratio,
            this_role_accepted + this_role_waiting + 1,
            other_role_accepted,
            self._p[other_role]
        )

    def can_add(self, option, consider_waiting_list=True) -> bool:
        raise NotImplementedError()

    def waiting_list_for_option(self, option) -> Optional[int]:
        raise NotImplementedError()


@dataclass
class SimpleWaitingList(BaseWaitingList):
    """
    Limits registrations by checking if current ratio violation.
    In order to pass the beginning turbulence, use allow_first option
    """
    allow_first: int = None

    def __post_init__(self):
        super(SimpleWaitingList, self).__post_init__()
        if self.allow_first is None:
            self.allow_first = self.max_available

    def can_add(self, option, consider_waiting_list=True) -> bool:
        if consider_waiting_list and self.registration_stats[option].waiting:
            return False

        if option == COUPLE:
            return self.total_accepted + 2 <= self.max_available

        other_role = flip_role(option)
        this_role_accepted = self.registration_stats[option].accepted
        other_role_accepted = self.registration_stats[other_role].accepted
        other_role_total = self.registration_stats[other_role].total
        total_accepted = self.total_accepted

        if total_accepted + 1 > self.max_available:
            return False

        if total_accepted < self.allow_first:
            return True
        elif other_role_accepted == 0 and total_accepted >= self.allow_first:
            return False
        elif (this_role_accepted + 1) / other_role_total <= self.ratio:
            return True
        else:
            return False

    def waiting_list_for_option(self, option) -> Optional[float]:
        already_waiting = self.registration_stats[option].waiting
        if already_waiting:
            return self.probability_for_option(option)

        if self.can_add(option):
            return None
        else:
            return self.probability_for_option(option)


@dataclass
class ProbabilityWaitingList(BaseWaitingList):
    """
    Limits registrations by checking if probability of violating ratio.
    Gives a probability to get off the waiting list.
    """
    probability_threshold: float = 0.96

    def can_add(self, option, consider_waiting_list=True) -> bool:
        if consider_waiting_list and self.registration_stats[option].waiting:
            return False

        probability = self.probability_for_option(option)
        return probability >= self.probability_threshold

    def waiting_list_for_option(self, option) -> Optional[float]:
        probability = self.probability_for_option(option)
        if probability < self.probability_threshold:
            return probability
