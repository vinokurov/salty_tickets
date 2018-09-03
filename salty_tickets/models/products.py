from datetime import datetime
from typing import Dict, Set

from dataclasses import dataclass, field
from salty_tickets.forms import get_primary_personal_info_from_form, get_partner_personal_info_from_form
from salty_tickets.models.personal_info import PersonInfo
from salty_tickets.waiting_lists import AutoBalanceWaitingList, RegistrationStats, flip_role
from wtforms import Form as NoCsrfForm
from wtforms.fields import RadioField
from wtforms.validators import Optional
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE, ACCEPTED, WAITING
from salty_tickets.utils import string_to_key


@dataclass
class BaseProduct:
    name: str
    key: str = None
    info: str = None
    max_available: int = None
    base_price: float = 0
    image_url: str = None
    tags: Set = field(default_factory=set)
    registrations: list = field(default_factory=list)

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    def get_form_class(self):
        raise NotImplementedError()

    def parse_form(self, form):
        if form.get_product_by_key(self.key).add.data:
            return [PurchaseItem(name=self.name, product_key=self.key)]

    def get_available_quantity(self):
        if self.max_available is None:
            return None

        total_accepted = len([r for r in self.registrations if r.status == ACCEPTED])
        return self.max_available - total_accepted

    def added(self, product_form):
        return bool(product_form.add.data)

    def _create_base_registration(self):
        return ProductRegistration(name=self.name, product_key=self.key)


@dataclass
class PartnerProduct(BaseProduct):
    def needs_partner(self, event_form):
        product_data = event_form.get_product_by_key(self.key)
        return product_data.add.data == COUPLE

    def get_form_class(self):
        return PartnerProductForm

    def create_registration(self, person_info: PersonInfo, registered_by: PersonInfo):
        product_registration = self._create_base_registration()
        product_registration.name = f'{product_registration.name} / {person_info.dance_role} / {person_info.full_name}'
        product_registration.person = person_info
        product_registration.registered_by = registered_by
        return product_registration

    def parse_form(self, event_form):
        product_data = event_form.get_product_by_key(self.key)
        if self.added(product_data):
            if product_data.add.data == COUPLE:
                person_info = get_primary_personal_info_from_form(event_form)
                partner_info = get_partner_personal_info_from_form(event_form)
                person_info.dance_role = event_form.dance_role.data
                partner_info.dance_role = flip_role(person_info.dance_role)

                registration_1 = self.create_registration(person_info, person_info)
                registration_2 = self.create_registration(partner_info, person_info)

                return [registration_1, registration_2]

            elif product_data.add.data in [LEADER, FOLLOWER]:
                person_info = get_primary_personal_info_from_form(event_form)
                person_info.dance_role = product_data.add.data
                registration = self.create_registration(person_info, person_info)
                return [registration]




@dataclass
class WaitListedPartnerProduct(PartnerProduct):
    ratio: float = 100
    allow_first: int = None

    def __post_init__(self):
        super(WaitListedPartnerProduct, self).__post_init__()
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
            accepted=len([r for r in registered if r.status == ACCEPTED]),
            waiting=len([r for r in registered if r.status == WAITING]),
        )

    def get_available_quantity(self):
        if self.max_available is None:
            return None

        if self.waiting_list is None:
            raise LookupError('WorkShopProduct.waiting_list is not set up')

        total_accepted = self.waiting_list.registration_stats[LEADER].accepted \
                         + self.waiting_list.registration_stats[FOLLOWER].accepted
        return self.max_available - total_accepted


@dataclass
class WorkshopProduct(WaitListedPartnerProduct):
    start_datetime: datetime = None
    end_datetime: datetime = None

    level: str = None
    duration: str = None
    location: str = None
    teachers: str = None


class PartnerProductForm(NoCsrfForm):
    add = RadioField(label='Add', default='', validators=[Optional()], choices=[
        (LEADER, 'Leader'),
        (FOLLOWER, 'Follower'),
        (COUPLE, 'Couple'),
        ('', 'None')
    ])


@dataclass
class PartyProduct(PartnerProduct):
    start_datetime: datetime = None
    end_datetime: datetime = None
    location: str = None


@dataclass
class ProductRegistration:
    registered_by: PersonInfo = None
    person: PersonInfo = None
    partner: PersonInfo = None
    dance_role: str = None
    as_couple: bool = False
    status: str = None
    details: Dict = field(default_factory=dict)
    price: float = None
    paid: float = None
    date: datetime = None
    product_key: str = None
