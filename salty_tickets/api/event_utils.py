import typing

from salty_tickets import TicketsDAO
from salty_tickets.models.event import EventSummaryNumbers, Event
from salty_tickets.models.registrations import Registration
from salty_tickets.models.tickets import WorkshopTicket, TicketNumbers


def get_event_active_registrations(dao: TicketsDAO, event: Event) -> typing.List[Registration]:
    registrations = dao.query_registrations(event)
    return [r for r in registrations if r.active]


def allocate_registrations_by_ticket(event: Event, registrations: typing.List[Registration], tickets: typing.List[str] = None) -> typing.Dict[str, typing.List[Registration]]:
    ticket_registrations = {}
    for ticket_key in event.tickets:
        if tickets and ticket_key not in tickets:
            continue
        ticket_registrations[ticket_key] = [r for r in registrations if r.ticket_key == ticket_key]
    return ticket_registrations


def calculate_registration_numbers(event, registrations: typing.List[Registration]) -> EventSummaryNumbers:
    registrations = [r for r in registrations if r.active]
    persons = {r.person.full_name.lower(): r.person for r in registrations}.values()

    def location_to_tuple(location_dict):
        return tuple({k: v for k, v in location_dict.items() if k != 'query'}.items())

    return EventSummaryNumbers(
        persons_count=len(persons),
        workshops_accepted=len([r for r in registrations if not r.wait_listed
                                and isinstance(event.tickets[r.ticket_key], WorkshopTicket)]),
        countries_count=len(set([p.location.get('country_code') for p in persons])),
        locations_count=len(set([location_to_tuple(p.location) for p in persons])),
    )
