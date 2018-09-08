from datetime import datetime
# from typing import Set, List
import typing

from dataclasses import dataclass, field
from salty_tickets.forms import get_primary_personal_info_from_form, get_partner_personal_info_from_form
from salty_tickets.models.registrations import PersonInfo, ProductRegistration
from salty_tickets.waiting_lists import AutoBalanceWaitingList, RegistrationStats, flip_role
from wtforms import Form as NoCsrfForm
from wtforms.fields import RadioField
from wtforms.validators import Optional
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE, ACCEPTED, WAITING
from salty_tickets.utils.utils import string_to_key


@dataclass
class BaseProduct:
    name: str
    key: str = None
    info: str = None
    max_available: int = None
    base_price: float = 0
    image_url: str = None
    tags: typing.Set = field(default_factory=set)
    registrations: typing.List[ProductRegistration] = field(default_factory=list)

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    def get_form_class(self) -> NoCsrfForm:
        raise NotImplementedError()

    def parse_form(self, form) -> typing.List[ProductRegistration]:
        if self.added(form.get_product_by_key(self.key)):
            return [self._create_base_registration()]

    def get_available_quantity(self) -> typing.Optional[int]:
        if self.max_available is None:
            return None

        total_accepted = len([r for r in self.registrations if r.status == ACCEPTED])
        return self.max_available - total_accepted

    def added(self, product_form) -> bool:
        return bool(product_form.add.data)

    def _create_base_registration(self) -> ProductRegistration:
        return ProductRegistration(product_key=self.key)

    def item_info(self, registration: ProductRegistration) -> str:
        return self.name


@dataclass
class PartnerProduct(BaseProduct):
    def needs_partner(self, event_form):
        product_data = event_form.get_product_by_key(self.key)
        return product_data.add.data == COUPLE

    def get_form_class(self):
        return PartnerProductForm

    def create_registration(self, person_info: PersonInfo, registered_by: PersonInfo, dance_role):
        registration = self._create_base_registration()
        # registration.info = f'{self.name} / {dance_role.title()} / {person_info.full_name}'
        registration.person = person_info
        registration.registered_by = registered_by
        registration.dance_role = dance_role
        return registration

    def parse_form(self, event_form) -> typing.List[ProductRegistration]:
        product_data = event_form.get_product_by_key(self.key)
        if self.added(product_data):
            if product_data.add.data == COUPLE:
                person_1 = get_primary_personal_info_from_form(event_form)
                person_2 = get_partner_personal_info_from_form(event_form)

                dance_role = event_form.dance_role.data
                registration_1 = self.create_registration(person_1, person_1, dance_role)
                registration_2 = self.create_registration(person_2, person_1, flip_role(dance_role))

                registration_1.partner = person_2
                registration_2.partner = person_1

                return [registration_1, registration_2]

            elif product_data.add.data in [LEADER, FOLLOWER]:
                person_1 = get_primary_personal_info_from_form(event_form)
                dance_role = product_data.add.data
                registration = self.create_registration(person_1, person_1, dance_role)
                return [registration]
        return []

    def item_info(self, registration: ProductRegistration) -> str:
        return f'{self.name} / {registration.dance_role.title()} / {registration.person.full_name}'


@dataclass
class WaitListedPartnerProduct(PartnerProduct):
    ratio: float = 100
    allow_first: int = None

    @property
    def waiting_list(self) -> AutoBalanceWaitingList:
        return AutoBalanceWaitingList(
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
            registered = [r for r in self.registrations if r.as_couple and r.active]
        else:
            registered = [r for r in self.registrations if r.dance_role == option and r.active]
        return RegistrationStats(
            accepted=len([r for r in registered if r.status == ACCEPTED]),
            waiting=len([r for r in registered if r.status == WAITING]),
        )

    def get_available_quantity(self) -> typing.Optional[int]:
        if self.max_available is None:
            return None

        if self.waiting_list is None:
            raise LookupError('WorkShopProduct.waiting_list is not set up')

        total_accepted = self.waiting_list.registration_stats[LEADER].accepted \
                         + self.waiting_list.registration_stats[FOLLOWER].accepted
        return self.max_available - total_accepted

    def balance_waiting_list(self) -> typing.List[ProductRegistration]:
        balanced_registrations = []
        while self.waiting_list.needs_balancing():
            if self.waiting_list.needs_balancing(COUPLE):
                regs = self._get_first_waiting_couple()
                if not regs:
                    continue
                for r in regs:
                    r.status = ACCEPTED
                balanced_registrations += regs

            for role in [LEADER, FOLLOWER]:
                if self.waiting_list.needs_balancing(role):
                    reg = self._get_first_waiting(role)
                    reg.status = ACCEPTED
                    balanced_registrations += [reg]

        return balanced_registrations

    def _get_first_waiting_couple(self) -> typing.List[ProductRegistration]:
        for r1 in self.registrations:
            if r1.as_couple and (r1.status == WAITING) and r1.active:
                r2_list = [r for r in self.registrations if r.person == r1.partner and r.active]
                if r2_list:
                    r2 = r2_list[0]
                    if r2.status is WAITING:
                        return [r1, r2]
                return [r1]
        return []

    def _get_first_waiting(self, role: str) -> ProductRegistration:
        for r in self.registrations:
            if r.active and (r.dance_role == role) and (r.status == WAITING):
                return r



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
