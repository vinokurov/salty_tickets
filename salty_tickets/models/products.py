from datetime import date, datetime
from typing import Dict

from dataclasses import dataclass, field
from waiting_lists import AutoBalanceWaitingList, RegistrationStats
from wtforms import Form as NoCsrfForm, TextAreaField
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, \
    HiddenField, IntegerField, FloatField, RadioField, TextField
from wtforms.validators import Optional, ValidationError
from salty_tickets.constants import DANCE_ROLE, WORKSHOP_OPTIONS, REGISTRATION_STATUS
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
        self.waiting_list = AutoBalanceWaitingList(
            max_available=self.max_available,
            ratio=self.ratio,
            registration_stats={
                WORKSHOP_OPTIONS.LEADER: self._get_registration_stats_for_role(WORKSHOP_OPTIONS.LEADER),
                WORKSHOP_OPTIONS.FOLLOWER: self._get_registration_stats_for_role(WORKSHOP_OPTIONS.FOLLOWER),
                WORKSHOP_OPTIONS.COUPLE: self._get_registration_stats_for_role(WORKSHOP_OPTIONS.COUPLE),
            }
        )

    def _get_registration_stats_for_role(self, option):
        if option == WORKSHOP_OPTIONS.COUPLE:
            registered = [r for r in self.registrations if r.as_couple]
        else:
            registered = [r for r in self.registrations if r.dance_role == option]
        return RegistrationStats(
            accepted=len([r for r in registered if r.status == REGISTRATION_STATUS.ACCEPTED]),
            waiting=len([r for r in registered if r.status == REGISTRATION_STATUS.WAITING]),
        )

    def create_form(self):
        class RegularPartnerWorkshopForm(NoCsrfForm):
            product_name = self.name
            product_id = self.key
            info = self.info
            price = self.base_price
            add = RadioField(label='Add', default=WORKSHOP_OPTIONS.NONE, validators=[Optional()], choices=[
                (WORKSHOP_OPTIONS.LEADER, 'Leader'),
                (WORKSHOP_OPTIONS.FOLLOWER, 'Follower'),
                (WORKSHOP_OPTIONS.COUPLE, 'Couple'),
                (WORKSHOP_OPTIONS.NONE, 'None')
            ])
            # partner_token = StringField(label='Partner\'s registration token', validators=[PartnerTokenValid()])
            product_type = self.__class__.__name__
            workshop_date = self.start_datetime.date()
            workshop_time = self.start_datetime.time()
            workshop_location = self.location
            workshop_level = self.level
            workshop_price = self.base_price
            workshop_teachers = self.teachers
            waiting_lists = self.waiting_list.waiting_stats
            available_quantity = self.get_available_quantity()
            keywords = self.tags

            def needs_partner(self):
                return self.add.data == WORKSHOP_OPTIONS.COUPLE

        return RegularPartnerWorkshopForm

    def get_available_quantity(self):
        if self.max_available is None:
            return None

        if self.waiting_list is None:
            raise LookupError('WorkShopProduct.waiting_list is not set up')

        total_accepted = self.waiting_list.registration_stats[WORKSHOP_OPTIONS.LEADER].accepted \
                         + self.waiting_list.registration_stats[WORKSHOP_OPTIONS.FOLLOWER].accepted
        return self.max_available - total_accepted

    @classmethod
    def parse_form(cls, form_data):
        pass


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
