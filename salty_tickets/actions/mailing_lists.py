from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from itsdangerous import BadSignature
from salty_tickets.dao import TicketsDAO
from salty_tickets.tokens import RegistrationToken


@dataclass
class EmailUnsubscribeResponse(DataClassJsonMixin):
    success: bool
    status_text: str = ''


def do_email_unsubscribe(dao: TicketsDAO, registration_token: str):
    try:
        person = RegistrationToken().deserialize(dao, registration_token.strip())
    except BadSignature:
        return EmailUnsubscribeResponse(False, status_text='failed''Failed: user not found')

    if person is None:
        return EmailUnsubscribeResponse(False, status_text='failed''Failed: user not found')

    event_key = dao.get_person_event_key(person)
    email_settings = dao.get_event_email_settings(event_key)
    email_settings.undo_unsubscribe_email(person.email)
    dao.update_event_email_settings(email_settings)

    return EmailUnsubscribeResponse(
        False,
        'Email has been successfully unsubscribed from notifications'
    )
