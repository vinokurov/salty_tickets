import pytest
from salty_tickets.models.email_campaigns import EventEmailSettings
from salty_tickets.tests.conftest import TestTicketsDAO


@pytest.fixture()
def test_dao():
    return TestTicketsDAO()


def test_create_event_email_settings(test_dao):
    event_email_settings = EventEmailSettings(event_key='test_event')
    test_dao.new_event_email_settings(event_email_settings)

    event_email_settings_loaded = test_dao.get_event_email_settings('test_event')
    assert event_email_settings == event_email_settings_loaded


@pytest.fixture()
def event_email_settings(test_dao):
    event_email_settings = EventEmailSettings(event_key='test_event')
    test_dao.new_event_email_settings(event_email_settings)
    return event_email_settings


def test_unsubscribe_event_email_notifications(test_dao, event_email_settings):
    # unsubscribe one email
    email_1 = 'test@test.com'
    assert email_1 not in event_email_settings.unsubscribed_emails

    event_email_settings.unsubscribe_email(email_1)
    test_dao.update_event_email_settings(event_email_settings)

    event_email_settings = test_dao.get_event_email_settings(event_email_settings.event_key)
    assert email_1 in event_email_settings.unsubscribed_emails

    # unsubscribe one more email
    email_2 = 'test2@test.com'
    assert email_2 not in event_email_settings.unsubscribed_emails

    event_email_settings.unsubscribe_email(email_2)
    test_dao.update_event_email_settings(event_email_settings)

    event_email_settings = test_dao.get_event_email_settings(event_email_settings.event_key)
    assert email_1 in event_email_settings.unsubscribed_emails
    assert email_2 in event_email_settings.unsubscribed_emails

    # undo unsubscribe first email
    event_email_settings.undo_unsubscribe_email(email_1)
    test_dao.update_event_email_settings(event_email_settings)

    event_email_settings = test_dao.get_event_email_settings(event_email_settings.event_key)
    assert email_1 not in event_email_settings.unsubscribed_emails
    assert email_2 in event_email_settings.unsubscribed_emails

