import typing
from typing import List, Dict

from dataclasses import dataclass, field
from salty_tickets.models.registrations import Registration


@dataclass
class TicketPricer:
    """
    A class to calculate prices for the selected tickets
    """
    event_tickets: dict = field(default_factory=dict)
    price_rules: list = field(default_factory=list)

    def __post_init__(self):
        if not self.price_rules:
            self.price_rules.append(BasePriceRule())

    def price_all(self, registrations: List[Registration],
                  prior_registrations: List[Registration] = None):
        if prior_registrations is None:
            prior_registrations = []
        priced_regs = []
        for reg in registrations:
            reg.price = self.optimal_price(reg, registrations + prior_registrations,
                                           priced_registrations=priced_regs + prior_registrations)
            priced_regs.append(reg)

    def optimal_price(self, registration: Registration,
                      registration_list: List[Registration],
                      priced_registrations: List[Registration]) -> float:
        possible_prices = [rule.price(registration, registration_list, self.event_tickets, priced_registrations)
                           for rule in self.price_rules]
        possible_prices = [p for p in possible_prices if p is not None]
        if possible_prices:
            price = min(possible_prices)
            return price

    @classmethod
    def from_event(cls, event):
        pricing_rules = [PRICING_RULES[k['name']](**k['kwargs']) for k in event.pricing_rules]
        return cls(event.tickets, pricing_rules)


class BasePriceRule:
    def price(self, registration, registration_list, event_tickets, priced_registrations) -> float:
        return event_tickets[registration.ticket_key].base_price

    @classmethod
    def filter_tickets_by_tag(cls, event_tickets, tag):
        return [k for k, p in event_tickets.items() if tag in p.tags]


@dataclass
class TaggedBasePriceRule(BasePriceRule):
    tag: str

    def price(self, registration, registration_list, event_tickets, priced_registrations) -> float:
        applicable_ticket_keys = self.filter_tickets_by_tag(event_tickets, self.tag)
        if registration.ticket_key in applicable_ticket_keys:
            return super(TaggedBasePriceRule, self).price(registration, registration_list, event_tickets, priced_registrations)


@dataclass
class SpecialPriceIfMoreThanPriceRule(BasePriceRule):
    more_than: int
    special_price: float
    tag: str

    def price(self, registration, registration_list, event_tickets, priced_registrations) -> float:
        applicable_ticket_keys = [k for k, p in event_tickets.items()
                                   if self.tag in p.tags]
        if registration.ticket_key in applicable_ticket_keys:
            already = [r for r in priced_registrations if r.ticket_key in applicable_ticket_keys]

            # make sure we count only purchase items for one person
            person = registration.person
            if person:
                already = [r for r in already if r.person == person]

            if len(already) >= self.more_than:
                return self.special_price


@dataclass
class CombinationsPriceRule(BasePriceRule):
    tag: str
    count_prices: Dict[str, float]

    def price(self, registration, registration_list, event_tickets, priced_registrations) -> float:
        applicable_ticket_keys = [k for k, p in event_tickets.items()
                                   if self.tag in p.tags]
        if registration.ticket_key in applicable_ticket_keys:
            # make sure we count only purchase items for one person
            person = registration.person
            if person:
                counted_regs = [r for r in registration_list
                                if r.ticket_key in applicable_ticket_keys
                                and r.person == person]
                count = len(counted_regs)
                if str(count) in self.count_prices:
                    return self.count_prices[str(count)] / count


@dataclass
class MindTheShagPriceRule(BasePriceRule):
    price_station: float
    price_clinic: float
    price_station_extra: float
    price_cheaper_station_extra: float

    tag_station: str = 'station'
    tag_fast_train: str = 'train'
    tag_party: str = 'party'
    tag_clinic: str = 'clinic'
    tag_cheaper: str = 'cheaper_station'

    tag_station_discount_3: str = 'station_discount_3'
    tag_station_discount_2: str = 'station_discount_2'
    tag_includes_parties: str = 'includes_parties'

    def price(self, registration, registration_list, event_tickets, priced_registrations, skip_prior=False) -> float:
        person = registration.person
        if person:
            person_registrations = [r for r in registration_list if r.person == person]
            person_priced_registrations = [r for r in priced_registrations if r.person == person]
        else:
            person_registrations = registration_list
            person_priced_registrations = priced_registrations

        registration_keys = [r.ticket_key for r in person_registrations]
        station_keys = self.filter_tickets_by_tag(event_tickets, self.tag_station)
        fast_train_station_keys = self.filter_tickets_by_tag(event_tickets, self.tag_fast_train)
        party_keys = self.filter_tickets_by_tag(event_tickets, self.tag_party)
        clinic_keys = self.filter_tickets_by_tag(event_tickets, self.tag_clinic)
        cheaper_keys = self.filter_tickets_by_tag(event_tickets, self.tag_cheaper)

        stations_priced_count = len([r for r in person_priced_registrations if r.ticket_key in station_keys])

        if registration.ticket_key in clinic_keys:
            if self._has_tags(registration_keys, event_tickets, {self.tag_station_discount_3}):
                if stations_priced_count < 3:
                    return self.price_clinic - self.price_station_extra
                else:
                    return self.price_clinic
            else:
                return self.price_clinic

        elif registration.ticket_key in station_keys:
            if self._has_tags(registration_keys, event_tickets, {self.tag_station_discount_2}):
                if registration.ticket_key in fast_train_station_keys:
                    return 0.0
                elif registration.ticket_key in cheaper_keys:
                    return self.price_cheaper_station_extra
                else:
                    return self.price_station_extra

            elif self._has_tags(registration_keys, event_tickets, {self.tag_station_discount_3}):
                if stations_priced_count < 3:
                    if registration.ticket_key in cheaper_keys:
                        return self.price_cheaper_station_extra - self.price_station_extra
                    else:
                        return 0
                elif registration.ticket_key in cheaper_keys:
                    return self.price_cheaper_station_extra
                else:
                    return self.price_station_extra
            else:
                # return self.price_station
                return event_tickets[registration.ticket_key].base_price

        elif registration.ticket_key in party_keys:
            if self._has_tags(registration_keys, event_tickets, {self.tag_includes_parties}):
                return 0.0
            else:
                return event_tickets[registration.ticket_key].base_price

        elif 'pass' in event_tickets[registration.ticket_key].tags:
            if skip_prior:
                prior_registrations = []
            else:
                prior_registrations = [r for r in person_priced_registrations if r.active]

            if not prior_registrations:
                return event_tickets[registration.ticket_key].base_price
            else:
                # get actual price of the prior registrations
                priced_regs = []
                prior_total_price = 0
                for reg in prior_registrations:
                    prior_total_price += self.price(reg, prior_registrations, event_tickets,
                                                    priced_regs, skip_prior=True) or 0
                    priced_regs.append(reg)

                # get price of the prior registrations with the new pass
                prior_registrations_with_new_pass = [registration] + [r for r in prior_registrations
                                                                      if not 'pass' in event_tickets[r.ticket_key].tags]
                priced_regs = []
                prior_total_price_new = 0
                for reg in prior_registrations_with_new_pass:
                    prior_total_price_new += self.price(reg, prior_registrations_with_new_pass,
                                                        event_tickets, priced_regs, skip_prior=True) or 0
                    priced_regs.append(reg)

                return prior_total_price_new - prior_total_price



    @classmethod
    def _has_tags(cls, registration_keys, event_tickets, tags):
        if type(tags) == str:
            tags = {tags}
        for reg_key in registration_keys:
            if tags.intersection(event_tickets[reg_key].tags):
                return True


PRICING_RULES = {
    'special_price_if_more_than': SpecialPriceIfMoreThanPriceRule,
    'combination': CombinationsPriceRule,
    'mind_the_shag': MindTheShagPriceRule,
    'tagged_base': TaggedBasePriceRule,
}
