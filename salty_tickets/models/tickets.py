from datetime import datetime
import typing

from dataclasses import dataclass, field
from salty_tickets.forms import get_primary_personal_info_from_form, get_partner_personal_info_from_form, RawField
from salty_tickets.models.registrations import Person, Registration
from salty_tickets.waiting_lists import SimpleWaitingList, RegistrationStats, flip_role
from wtforms import Form as NoCsrfForm
from wtforms.fields import RadioField
from wtforms.validators import Optional
from salty_tickets.constants import LEADER, FOLLOWER, COUPLE
from salty_tickets.utils.utils import string_to_key


@dataclass
class RoleNumbers:
    accepted: typing.Optional[int] = 0
    waiting: typing.Optional[int] = None
    is_wait_listed: bool = False
    waiting_probability: typing.Optional[int] = None


@dataclass
class TicketNumbers:
    accepted: typing.Optional[int] = 0
    remaining: typing.Optional[int] = None
    roles: typing.Dict[str, RoleNumbers] = field(default_factory=dict)


@dataclass
class Ticket:
    name: str
    key: str = None
    info: str = None
    max_available: int = None
    base_price: float = 0
    image_url: str = None
    tags: typing.Set = field(default_factory=set)
    # registrations: typing.List[Registration] = field(default_factory=list)
    numbers: typing.Optional[TicketNumbers] = None

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    def get_form_class(self) -> type:
        raise NotImplementedError()

    def parse_form(self, form) -> typing.List[Registration]:
        if self.is_added(form.get_item_by_key(self.key)):
            return [self._create_base_registration()]

    def get_available_quantity(self) -> typing.Optional[int]:
        return self.numbers.remaining

    @classmethod
    def is_added(cls, ticket_form) -> bool:
        return bool(ticket_form.add.data)

    def _create_base_registration(self) -> Registration:
        return Registration(ticket_key=self.key)

    def item_info(self, registration: Registration) -> str:
        return self.name

    def calculate_accepted(self, registrations) -> int:
        return len([r for r in registrations if not r.wait_listed and r.active])

    def calculate_remaining(self, registrations):
        if self.max_available is None:
            return None
        total_accepted = self.calculate_accepted(registrations)
        return self.max_available - total_accepted

    def calculate_ticket_numbers(self, registrations) -> TicketNumbers:
        return TicketNumbers(
            accepted=self.calculate_accepted(registrations),
            remaining=self.calculate_remaining(registrations)
        )


class PartnerTicket(Ticket):
    def needs_partner(self, event_form) -> bool:
        ticket_data = event_form.get_item_by_key(self.key)
        return ticket_data.add.data == COUPLE

    def get_form_class(self) -> type:
        return PartnerTicketForm

    def create_registration(self, person_info: Person, registered_by: Person, dance_role) -> Registration:
        registration = self._create_base_registration()
        # registration.info = f'{self.name} / {dance_role.title()} / {person_info.full_name}'
        registration.person = person_info
        registration.registered_by = registered_by
        registration.dance_role = dance_role
        return registration

    def parse_form(self, form) -> typing.List[Registration]:
        ticket_data = form.get_item_by_key(self.key)
        if self.is_added(ticket_data):
            if ticket_data.add.data == COUPLE:
                person_1 = get_primary_personal_info_from_form(form) or Person('You', '')
                person_2 = get_partner_personal_info_from_form(form) or Person('Partner', '')

                dance_role = form.dance_role.data
                registration_1 = self.create_registration(person_1, person_1, dance_role)
                registration_2 = self.create_registration(person_2, person_1, flip_role(dance_role))

                registration_1.partner = person_2
                registration_2.partner = person_1
                return [registration_1, registration_2]

            elif ticket_data.add.data in [LEADER, FOLLOWER]:
                person_1 = get_primary_personal_info_from_form(form) or Person('You', '')
                dance_role = ticket_data.add.data
                registration = self.create_registration(person_1, person_1, dance_role)
                return [registration]
        return []

    def item_info(self, registration: Registration) -> str:
        info_list = [self.name]
        if registration.dance_role:
            info_list.append(registration.dance_role.title())
        if registration.person:
            info_list.append(registration.person.full_name)

        return ' / '.join(info_list)


@dataclass
class WaitListedPartnerTicket(PartnerTicket):
    ratio: float = 100
    allow_first: int = None
    expected_leads: int = None
    expected_follows: int = None

    def parse_form(self, form) -> typing.List[Registration]:
        regs = super(WaitListedPartnerTicket, self).parse_form(form)
        ticket_data = form.get_item_by_key(self.key)
        if self.is_added(ticket_data):
            role = ticket_data.add.data
            if not self.waiting_list.can_add(role):
                for r in regs:
                   r.wait_listed = True
        return regs

    def item_info(self, registration: Registration) -> str:
        info = super(WaitListedPartnerTicket, self).item_info(registration)
        if registration.wait_listed:
            info = f'Waiting List: {info}'

        return info

    @property
    def waiting_list(self) -> SimpleWaitingList:
        return self._create_waiting_list(
            registration_stats={
                LEADER: self._get_registration_stats_for_role(LEADER),
                FOLLOWER: self._get_registration_stats_for_role(FOLLOWER),
                COUPLE: self._get_registration_stats_for_role(COUPLE),
            },
        )

    def _create_waiting_list(self, registration_stats) -> SimpleWaitingList:
        return SimpleWaitingList(
            max_available=self.max_available,
            ratio=self.ratio,
            registration_stats=registration_stats,
            allow_first=self.allow_first,
            expected_leads=self.expected_leads,
            expected_follows=self.expected_follows,
        )

    def _get_registration_stats_for_role(self, option: str) -> RegistrationStats:
        return RegistrationStats(
            accepted=self.numbers.roles[option].accepted,
            waiting=self.numbers.roles[option].waiting,
        )

    def get_available_quantity(self) -> typing.Optional[int]:
        if self.max_available is None:
            return None

        if self.waiting_list is None:
            raise LookupError('WorkShopTicket.waiting_list is not set up')

        total_accepted = self.waiting_list.registration_stats[LEADER].accepted \
                         + self.waiting_list.registration_stats[FOLLOWER].accepted
        return self.max_available - total_accepted

    def balance_waiting_list(self, registrations: typing.List[Registration]) -> typing.List[Registration]:
        balanced_registrations = []
        while self.waiting_list.needs_balancing():
            if self.waiting_list.needs_balancing(COUPLE):
                regs = self._get_first_waiting_couple(registrations)
                if not regs:
                    continue
                for r in regs:
                    r.wait_listed = False
                balanced_registrations += regs
                self.numbers = self.calculate_ticket_numbers(registrations)

            for role in [LEADER, FOLLOWER]:
                if self.waiting_list.needs_balancing(role):
                    reg = self._get_first_waiting(role, registrations)
                    reg.wait_listed = False
                    balanced_registrations += [reg]
                    self.numbers = self.calculate_ticket_numbers(registrations)

        return balanced_registrations

    def _get_first_waiting_couple(self, registrations: typing.List[Registration]) -> typing.List[Registration]:
        for r1 in registrations:
            if r1.as_couple and r1.wait_listed and r1.active:
                r2_list = [r for r in registrations if r.person == r1.partner and r.active]
                if r2_list:
                    r2 = r2_list[0]
                    if r2.wait_listed:
                        return [r1, r2]
                return [r1]
        return []

    def _get_first_waiting(self, role: str, registrations: typing.List[Registration]) -> Registration:
        for r in registrations:
            if r.active and (r.dance_role == role) and r.wait_listed:
                return r

    def apply_extra_partner(self, this_registration: Registration,
                            extra_registrations: typing.List[Registration]):
        if self.waiting_list.can_add(COUPLE):
            available_extra_regs = [r for r in extra_registrations
                                    if r.ticket_key == self.key and r.active and not r.partner
                                    and r.dance_role == flip_role(this_registration.dance_role)]
            if available_extra_regs:
                extra_reg = available_extra_regs[0]
                this_registration.partner = extra_reg.person
                this_registration.wait_listed = False
                extra_reg.partner = this_registration.person
                extra_reg.wait_listed = False
                return extra_reg

    def calculate_ticket_numbers(self, registrations: typing.List[Registration]) -> TicketNumbers:
        roles = {}
        for option in [LEADER, FOLLOWER, COUPLE]:
            if option == COUPLE:
                registered = [r for r in registrations if r.as_couple and r.active]
            else:
                registered = [r for r in registrations if r.dance_role == option and r.active]
            accepted = len([r for r in registered if not r.wait_listed])
            waiting = len([r for r in registered if r.wait_listed])
            roles[option] = RoleNumbers(accepted=accepted, waiting=waiting)

        waiting_list = self._create_waiting_list({k: RegistrationStats(accepted=v.accepted, waiting=v.waiting)
                                                  for k, v in roles.items()})

        for option in [LEADER, FOLLOWER, COUPLE]:
            roles[option].is_wait_listed = not waiting_list.can_add(option)
            roles[option].waiting_probability = not waiting_list.probability_for_option(option)

        return TicketNumbers(
            accepted=self.calculate_accepted(registrations),
            remaining=self.calculate_remaining(registrations),
            roles=roles
        )


@dataclass
class WorkshopTicket(WaitListedPartnerTicket):
    start_datetime: datetime = None
    end_datetime: datetime = None

    level: str = None
    duration: str = None
    location: str = None
    teachers: str = None


class PartnerTicketForm(NoCsrfForm):
    add = RadioField(label='Add', default='', validators=[Optional()], choices=[
        (LEADER, 'Leader'),
        (FOLLOWER, 'Follower'),
        (COUPLE, 'Couple'),
        ('', 'None')
    ])


@dataclass
class PartyTicket(PartnerTicket):
    start_datetime: datetime = None
    end_datetime: datetime = None
    location: str = None

    def item_info(self, registration: Registration) -> str:
        info_list = [self.name]
        if registration.person:
            info_list.append(registration.person.full_name)

        return ' / '.join(info_list)


@dataclass
class FestivalPassTicket(PartnerTicket):
    includes: typing.Dict = field(default_factory=dict)

    def item_info(self, registration: Registration) -> str:
        info_list = [self.name]
        if registration.person:
            info_list.append(registration.person.full_name)

        return ' / '.join(info_list)
