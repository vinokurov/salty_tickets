from typing import List, Dict

from salty_tickets.models.event import Event
from salty_tickets.models.tickets import Ticket
from salty_tickets.models.registrations import Registration


def validate_registrations(event: Event, registrations: List[Registration]):
    errors = {}
    for rule in event.validation_rules:
        rule_func = VALIDATION_RULES[rule['name']]
        _error = rule_func(registrations, event.tickets, **rule['kwargs'])
        if _error:
            errors['Registration'] = [_error]
    return errors


def errors_at_least_any_with_tag(registrations: List[Registration],
                                 products: Dict[str, Ticket],
                                 tag, count=1, error_text=None):
    if registrations:
        primary = registrations[0].registered_by
        matching_products = [products[r.ticket_key] for r in registrations
                             if tag in products[r.ticket_key].tags
                             and r.person == primary]
        if 0 < len(matching_products) < count:
            return error_text

        partner_products = [products[r.ticket_key] for r in registrations
                            if tag in products[r.ticket_key].tags
                            and r.person != primary]
        if 0 < len(partner_products) < count:
            return error_text


def errors_if_overlapping(registrations: List[Registration],
                          products: Dict[str, Ticket],
                          tag, error_text=None):
    if registrations:
        primary = registrations[0].registered_by
        if primary:
            matching_products = [products[r.ticket_key] for r in registrations
                                 if tag in products[r.ticket_key].tags
                                 and r.person == primary]
            start_times = [p.start_datetime for p in matching_products if hasattr(p, 'start_datetime')]
            if len(start_times) > len(set(start_times)):
                return error_text

            partner_products = [products[r.ticket_key] for r in registrations
                                if tag in products[r.ticket_key].tags
                                and r.person != primary]
            start_times = [p.start_datetime for p in partner_products if hasattr(p, 'start_datetime')]
            if len(start_times) > len(set(start_times)):
                return error_text


def mind_the_shag_validator(registrations: List[Registration],
                            tickets: Dict[str, Ticket],
                            tag, error_text=None):
    if registrations:
        persons = []
        primary = registrations[0].registered_by
        persons.append(primary)
        partner_registrations = [r for r in registrations if r.person!=primary]
        if partner_registrations:
            persons.append(partner_registrations[0].person)

        for person in persons:
            # add all parties if required
            registration_keys = [r.ticket_key for r in registrations if r.person == person]
            if _has_tags(registration_keys, tickets, 'includes_parties'):
                for party_key in ['friday_party', 'saturday_party', 'sunday_party']:
                    if party_key not in registration_keys:
                        registrations.append(Registration(
                            registered_by=primary,
                            person=person,
                            ticket_key=party_key,
                        ))

        for person in persons:
            registration_keys = [r.ticket_key for r in registrations if r.person == person]
            stations_count = len([k for k in registration_keys if 'station' in tickets[k].tags])
            if _has_tags(registration_keys, tickets, 'station_discount_3'):
                if stations_count < 3:
                    return 'You need to choose at least 3 stations'
            elif _has_tags(registration_keys, tickets, 'station_discount_2'):
                if not {'shag_abc', 'shag_essentials'}.intersection(set(registration_keys)):
                    return 'You need to select "Shag ABC" and "Shag Essentials"'
            elif len({'shag_abc', 'shag_essentials'}.intersection(set(registration_keys))) == 2:
                registrations.append(
                    Registration(
                        registered_by=primary,
                        person=person,
                        ticket_key='shag_novice_no_parties',
                    )
                )


def _has_tags(registration_keys_list, tickets_dict, tags):
    if type(tags) == str:
        tags = {tags}
    for ticket_key in registration_keys_list:
        if set(tickets_dict[ticket_key].tags).intersection(tags):
            return True

VALIDATION_RULES = {
    'at_least_any_with_tag': errors_at_least_any_with_tag,
    'non_overlapping': errors_if_overlapping,
    'mind_the_shag': mind_the_shag_validator,
}
