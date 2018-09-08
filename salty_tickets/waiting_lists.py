from typing import Dict, Optional

from dataclasses import dataclass, field
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE


@dataclass
class RegistrationStats:
    accepted: int = 0
    waiting: int = 0


def flip_role(role):
    return {
        LEADER: FOLLOWER,
        FOLLOWER: LEADER,
    }[role]


@dataclass
class AutoBalanceWaitingList:
    max_available: int
    ratio: float
    allow_first: int = None
    registration_stats: Dict[str, RegistrationStats] = field(default_factory=dict)

    def __post_init__(self):
        if self.allow_first is None:
            self.allow_first = self.max_available

        for o in [LEADER, FOLLOWER, COUPLE]:
            if o not in self.registration_stats:
                self.registration_stats[o] = RegistrationStats()

    @property
    def waiting_stats(self) -> Dict[str, RegistrationStats]:
        return {o: self.waiting_list_for_option(o) for o in [LEADER, FOLLOWER, COUPLE]}

    @property
    def has_waiting_list(self) -> bool:
        stats = self.registration_stats
        return stats[LEADER].waiting > 0 or stats[FOLLOWER].waiting > 0

    @property
    def current_ratio(self):
        round_digits = 3
        ratio = max(self.registration_stats[LEADER].accepted / self.registration_stats[FOLLOWER].accepted,
                    self.registration_stats[FOLLOWER].accepted / self.registration_stats[LEADER].accepted)
        return round(ratio, round_digits)

    def needs_balancing(self, option: str = None) -> bool:
        if option is None:
            return any([self.needs_balancing(o) for o in [LEADER, FOLLOWER, COUPLE]])
        else:
            return self.can_add(option) and self.registration_stats[option].waiting > 0

    def can_add(self, option) -> bool:
        if option == COUPLE:
            total_accepted = self.registration_stats[LEADER].accepted \
                             + self.registration_stats[FOLLOWER].accepted
            return total_accepted + 2 <= self.max_available
        else:
            other_role = flip_role(option)
            this_role_accepted = self.registration_stats[option].accepted
            other_role_accepted = self.registration_stats[other_role].accepted
            total_accepted = this_role_accepted + other_role_accepted

            if total_accepted + 1 <= self.max_available:
                if other_role_accepted == 0 and total_accepted < self.allow_first:
                    return True
                elif (this_role_accepted + 1) / other_role_accepted <= self.ratio:
                    return True

            return False

    def waiting_list_for_option(self, option) -> Optional[int]:
        already_waiting = self.registration_stats[option].waiting
        if already_waiting:
            return already_waiting
        else:
            if self.can_add(option):
                return None
            else:
                return 0
