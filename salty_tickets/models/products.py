from datetime import date, datetime
from typing import Dict

from dataclasses import dataclass, field
from waiting_lists import AutoBalanceWaitingList, RegistrationStats
from wtforms import Form as NoCsrfForm, TextAreaField
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, \
    HiddenField, IntegerField, FloatField, RadioField, TextField
from wtforms.validators import Optional, ValidationError
from salty_tickets.constants import REG_STATUS, LEADER, FOLLOWER, COUPLE
from salty_tickets.utils import string_to_key


@dataclass
class BaseProduct:
    name: str
    key: str = None
    info: str = None
    max_available: int = None
    base_price: float = 0
    image_url: str = None
    tags: set = field(default_factory=set)
    registrations: list = field(default_factory=list)

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    def create_form(self):
        raise NotImplementedError()

    @classmethod
    def parse_form(cls, form_data):
        raise NotImplemented()


@dataclass
class WorkshopProduct(BaseProduct):
    start_datetime: datetime = None
    end_datetime: datetime = None

    ratio: float = 100
    allow_first: int = None
    level: str = None
    duration: str = None
    location: str = None
    teachers: str = None

    def __post_init__(self):
        super(WorkshopProduct, self).__post_init__()
        self.waiting_list = AutoBalanceWaitingList(
            max_available=self.max_available,
            ratio=self.ratio,
            registration_stats={
                LEADER: self._get_registration_stats_for_role(LEADER),
                FOLLOWER: self._get_registration_stats_for_role(FOLLOWER),
                COUPLE: self._get_registration_stats_for_role(COUPLE),
            }
        )

    def _get_registration_stats_for_role(self, option):
        if option == COUPLE:
            registered = [r for r in self.registrations if r.as_couple]
        else:
            registered = [r for r in self.registrations if r.dance_role == option]
        return RegistrationStats(
            accepted=len([r for r in registered if r.status == REG_STATUS.ACCEPTED]),
            waiting=len([r for r in registered if r.status == REG_STATUS.WAITING]),
        )

    @staticmethod
    def get_form_class():
        return RegularPartnerWorkshopForm

    def get_available_quantity(self):
        if self.max_available is None:
            return None

        if self.waiting_list is None:
            raise LookupError('WorkShopProduct.waiting_list is not set up')

        total_accepted = self.waiting_list.registration_stats[LEADER].accepted \
                         + self.waiting_list.registration_stats[FOLLOWER].accepted
        return self.max_available - total_accepted

    @classmethod
    def parse_form(cls, form_data):
        pass


class RegularPartnerWorkshopForm(NoCsrfForm):
    add = RadioField(label='Add', default='', validators=[Optional()], choices=[
        (LEADER, 'Leader'),
        (FOLLOWER, 'Follower'),
        (COUPLE, 'Couple'),
        ('', 'None')
    ])


@dataclass
class TicketProduct(BaseProduct):
    pass


@dataclass
class ProductRegistration:
    full_name: str
    email: str
    dance_role: str = None
    as_couple: bool = False
    status: str = None
    details: Dict = field(default_factory=dict)
