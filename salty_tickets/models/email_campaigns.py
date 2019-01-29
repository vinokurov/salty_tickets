import typing

from dataclasses import dataclass, field


@dataclass
class EmailCampaign:
    name: str
    event_key: str
    sent_emails: typing.List


@dataclass
class EventEmailSettings:
    event_key: str
    unsubscribed_emails: typing.List = field(default_factory=list)

    def unsubscribe_email(self, email):
        self.unsubscribed_emails.append(email)

    def undo_unsubscribe_email(self, email):
        self.unsubscribed_emails.remove(email)


