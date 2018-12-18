import itertools
import typing

from dataclasses import dataclass
from salty_tickets.models.registrations import Payment, Discount, Person, DiscountCode
from wtforms import Form as NoCsrfForm, StringField, BooleanField
from salty_tickets.utils.utils import string_to_key


@dataclass
class DiscountProduct:
    name: str
    key: str = None
    info: str = None
    discount_value: float = None

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    def get_discount(self, tickets: typing.Dict, payment: Payment, form) -> typing.List:
        if self.is_added(form):
            return self._get_discount(tickets, payment, form)
        return []

    def _get_discount(self, tickets: typing.Dict, payment: Payment, form) -> typing.List:
        raise NotImplementedError()

    @classmethod
    def get_form_class(cls):
        return DiscountForm

    def is_added(self, form):
        discount_form = form.get_item_by_key(self.key)
        return discount_form.validated.data


class DiscountForm(NoCsrfForm):
    validated = BooleanField(default='')


class GroupDiscountForm(DiscountForm):
    name = StringField()
    code = StringField()


class CodeDiscountForm(DiscountForm):
    code = StringField()


def get_partner_from_payment_registrations(payment: Payment):
    for reg in payment.registrations:
        if reg.person != payment.paid_by:
            return reg.person


@dataclass
class FixedValueDiscountProduct(DiscountProduct):
    tag: str = None

    def _get_discount(self, tickets: typing.Dict, payment: Payment, form) -> typing.List:
        discount_form = form.get_item_by_key(self.key)
        discounts = []
        if self._applies_to_person(payment.paid_by, tickets, payment, discount_form):
            discounts.append(Discount(
                person=payment.paid_by,
                discount_key=self.key,
                description=self.info,
                value=self.discount_value
            ))

        partner = get_partner_from_payment_registrations(payment)
        if partner and self._applies_to_person(partner, tickets, payment, discount_form):
            discounts.append(Discount(
                person=partner,
                discount_key=self.key,
                description=self.info,
                value=self.discount_value
            ))
        return discounts

    def _applies_to_person(self, person: Person, tickets: typing.Dict, payment: Payment, discount_form) -> bool:
        registrations = [r for r in payment.registrations if r.person == person]
        if registrations:
            if self.tag:
                registration_tags = [tickets[r.ticket_key].tags for r in registrations]
                registration_tags = itertools.chain.from_iterable(registration_tags)
                return self.tag in registration_tags
            else:
                total_price = sum([r.price for r in registrations if r.price] or [0])
                return total_price > self.discount_value


@dataclass
class GroupDiscountProduct(FixedValueDiscountProduct):

    @classmethod
    def get_form_class(cls):
        return GroupDiscountForm

    def _get_discount(self, tickets: typing.Dict, payment: Payment, form) -> typing.List:
        discounts = super(GroupDiscountProduct, self)._get_discount(tickets, payment, form)
        discount_form = form.get_item_by_key(self.key)
        for d in discounts:
            d.discount_code = discount_form.code.data
        return discounts


@dataclass
class DiscountRule:
    info: str = 'Discount'

    def get_discount(self, tickets: typing.Dict, payment: Payment, person: Person, form) -> Discount:
        raise NotImplementedError()

    @classmethod
    def items_price(cls, items):
        return sum([i.price for i in items if i.price] or [0])


@dataclass
class FreeRegistrationDiscountRule(DiscountRule):
    def get_discount(self, tickets: typing.Dict, payment: Payment, person: Person, form) -> Discount:
        registrations = [r for r in payment.registrations if r.person == person]
        total_price = self.items_price(registrations)
        return Discount(
            person=person,
            value=total_price,
            description=self.info,
        )


@dataclass
class FreeAllDiscountRule(DiscountRule):
    def get_discount(self, tickets: typing.Dict, payment: Payment, person: Person, form) -> Discount:
        registrations = [r for r in payment.registrations if r.person == person]
        purchases = [p for p in payment.purchases if p.person == person]
        total_price = self.items_price(registrations + purchases)
        return Discount(
            person=person,
            value=total_price,
            description=self.info,
        )


@dataclass
class FreePartiesDiscountRule(DiscountRule):
    def get_discount(self, tickets: typing.Dict, payment: Payment, person: Person, form) -> Discount:
        discount_price = 0
        registrations = [r for r in payment.registrations if r.person == person]
        for reg in registrations:
            ticket = tickets[reg.ticket_key]
            if set(ticket.tags).intersection({'party', 'party_pass'}):
                discount_price += reg.price
            elif 'includes_parties' in ticket.tags:
                if reg.price >= tickets['party_pass'].base_price:
                    discount_price += tickets['party_pass'].base_price

        if discount_price:
            return Discount(
                person=person,
                value=discount_price,
                description=self.info,
            )


@dataclass
class FreeFullPassDiscountRule(DiscountRule):

    def get_discount(self, tickets: typing.Dict, payment: Payment, person: Person, form) -> Discount:
        discount_price = 0
        registrations = [r for r in payment.registrations if r.person == person]
        for reg in registrations:
            ticket = tickets[reg.ticket_key]
            if 'pass' in ticket.tags:
                discount_price += reg.price
                break

        if discount_price:
            return Discount(
                person=person,
                value=discount_price,
                description=self.info,
            )


def get_discount_rule_from_code(discount_code: DiscountCode) -> DiscountRule:
    return DISCOUNT_RULES[discount_code.discount_rule](info=discount_code.info)


@dataclass
class CodeDiscountProduct(DiscountProduct):
    discount_rule: DiscountRule = None
    discount_code: DiscountCode = None
    applies_to_couple: bool = False

    @classmethod
    def get_form_class(cls):
        return CodeDiscountForm

    def _get_discount(self, tickets: typing.Dict, payment: Payment, form) -> typing.List:
        discounts = []

        discount = self.discount_rule.get_discount(tickets, payment, payment.paid_by, form)
        if discount:
            discount.discount_key = self.key
            discount.discount_code = form.get_item_by_key(self.key).code.data
            discounts.append(discount)

        if self.discount_code is not None:
            applies_to_couple = self.discount_code.applies_to_couple
        else:
            applies_to_couple = self.applies_to_couple

        if applies_to_couple:
            partner = get_partner_from_payment_registrations(payment)
            if partner:
                discount = self.discount_rule.get_discount(tickets, payment, partner, form)
                if discount:
                    discount.discount_key = self.key
                    discount.discount_code = form.get_item_by_key(self.key).code.data
                    discounts.append(discount)
        return discounts


DISCOUNT_RULES = {
    'free_full_pass': FreeFullPassDiscountRule,
    'free_registration': FreeRegistrationDiscountRule,
    'free_party_pass': FreePartiesDiscountRule,
    'all_free': FreeAllDiscountRule,
}
