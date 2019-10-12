from salty_tickets.config import MONGO
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.tickets import WorkshopTicket, PartyTicket

dao = TicketsDAO(host=MONGO)
event = dao.get_event_by_key('mind_the_shag_2019')


def iter_active_regs(_ticket):
    for r in _ticket.registrations:
        if r.active:
            yield r


persons = {}


def init_person(_person):
    if _person not in persons:
        persons[_person.name] = {'workshops': [], 'parties': [], 'extras': [], 'email': _person.email}


for k, ticket in event.tickets.items():
    if isinstance(ticket, WorkshopTicket):
        for r in iter_active_regs(ticket):
            init_person(r.person)
            persons[r.person.full_name]['workshops'].append({ticket.key: r.dance_role})

    elif isinstance(ticket, PartyTicket):
        for r in iter_active_regs(ticket):
            init_person(r.person)
            persons[r.person.full_name]['parties'].append(ticket.key)

for person in persons:
    has_workshops = len(person['workshops']) > 0
    has_all_parties = len(person['parties']) == 3

    if has_workshops and has_all_parties:
        bracelet = 'Workshops & All Parties'
    elif has_all_parties:
        bracelet = 'All Parties'
    else:
        opts = []
        if has_workshops:
            opts += ['Workshops']
        if 'friday_party' in person['parties']:
            opts += ['Friday']
        elif 'saturday_party' in person['parties']:
            opts += ['Saturday']
        elif 'sunday_party' in person['parties']:
            opts += ['Sunday']
        bracelet = ', '.join(opts)
    person['bracelet'] = bracelet
