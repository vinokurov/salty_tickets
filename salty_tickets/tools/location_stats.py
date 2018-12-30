from pprint import pprint

from salty_tickets.config import MONGO
from salty_tickets.dao import TicketsDAO

dao = TicketsDAO(host=MONGO)
event = dao.get_event_by_key('mind_the_shag_2019')


def location_to_tuple(location_dict):
    return tuple({k: v for k, v in location_dict.items() if k != 'query'}.items())


def get_stats():
    registrations = []
    for p_key, p in event.tickets.items():
        registrations = registrations + p.registrations
    registrations = [r for r in registrations if r.active]
    persons = {r.person.full_name.lower(): r.person for r in registrations}.values()

    countries = {}
    locations = {}

    for person in persons:
        country = person.location['country']
        countries[country] = countries.get(country, 0) + 1

        location_key = location_to_tuple(person.location)
        locations[location_key] = locations.get(location_key, 0) + 1

    return countries, locations


if __name__ == '__main__':
    countries, locations = get_stats()
    pprint(countries)
    pprint(locations)
