import inspect
from collections import namedtuple

import math

from itsdangerous import BadSignature
from salty_tickets.database import db_session
from salty_tickets.discounts import discount_users
from salty_tickets.tokens import order_product_deserialize, order_product_token_expired
from sqlalchemy import asc
from sqlalchemy.orm import aliased
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, \
    HiddenField, IntegerField, FloatField, RadioField, TextField
from wtforms.validators import Optional, ValidationError

from salty_tickets.models import Product, ProductParameter, OrderProduct, DANCE_ROLE_FOLLOWER, DANCE_ROLE_LEADER, Order, \
    ORDER_STATUS_PAID, OrderProductDetail, ORDER_PRODUCT_STATUS_ACCEPTED, ORDER_PRODUCT_STATUS_WAITING, Registration, \
    SignupGroup, group_order_product_mapping, SIGNUP_GROUP_PARTNERS, PaymentItem, RegistrationGroup
import json


def flip_role(dance_role):
    if dance_role == DANCE_ROLE_FOLLOWER:
        return DANCE_ROLE_LEADER
    else:
        return DANCE_ROLE_FOLLOWER


class BaseProduct:
    name = ''
    info = ''
    max_available = 0
    price = None
    image_url = None
    waiting_list_price = None
    keywords=''
    _basic_attrs = ['name', 'info', 'max_available', 'price', 'image_url']

    def __init__(self, name, **kwargs):
        self.name = name

        # copy/paste from the sqlalchemy declarative constructor
        cls_ = type(self)
        for k in kwargs:
            if not hasattr(cls_, k):
                raise TypeError(
                    "%r is an invalid keyword argument for %s" %
                    (k, cls_.__name__))
            setattr(self, k, kwargs[k])

    def get_form(self):
        raise NotImplementedError()

    @property
    def model(self):
        kwargs = {a: getattr(self, a) for a in self._basic_attrs}
        kwargs['product_type'] = self.__class__.__name__
        kwargs['parameters_dict'] = self._parameters_dict
        return Product(**kwargs)

    @classmethod
    def from_model(cls, db_model):
        assert isinstance(db_model, Product)
        kwargs = {a: getattr(db_model, a) for a in cls._basic_attrs}

        for p in db_model.parameters:
            kwargs[p.parameter_name] = p.parameter_value

        product = cls(**kwargs)
        return product

    @property
    def _parameters_dict(self):
        cls = type(self)
        attrs = inspect.getmembers(cls, lambda a: not (inspect.ismethod(a) or inspect.isfunction(a) or isinstance(a, property)))
        attrs = [a[0] for a in attrs if not(a[0].startswith('_') or a[0].endswith('_'))
                                     and not a[0] in self._basic_attrs]
        params_dict = {a: getattr(self, a) for a in attrs}
        return params_dict

    def get_total_price(self, product_model, product_form, form):
        raise NotImplementedError()

    def get_waiting_list_price(self, product_model, total_price):
        if self.waiting_list_price:
            return float(self.waiting_list_price)
        else:
            return total_price

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_model, product_form, form)
        status =  ORDER_PRODUCT_STATUS_ACCEPTED
        order_product = OrderProduct(product_model, price, status=status)
        return order_product

    def get_payment_item(self, order_product):
        payment_item = PaymentItem()
        if order_product.status == ORDER_PRODUCT_STATUS_WAITING:
            amount = min(order_product.price,
                         self.get_waiting_list_price(order_product.product, order_product.price))
            payment_item.amount = amount
            if amount:
                payment_item.description = 'Refundable deposit'

        else:
            payment_item.amount = order_product.price
        payment_item.order_product = order_product
        return payment_item



def get_total_paid(product_model):
    return product_model.product_orders.join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID).count()


class ProductDiscountPricesMixin:
    discount_prices = None
    discount_persons = None
    discount_amounts = None

    def get_discount_price_by_key(self, key):
        discount_prices_dict = json.loads(self.discount_prices)
        return discount_prices_dict[key]

    def get_discount_price(self, product_model, product_form, order_form, name=None):
        discount_prices = [
            self.get_discount_price_for_keys(order_form),
            self.get_discount_price_for_person(product_form, order_form, name),
            self.get_discount_price_for_amount(product_model, product_form, order_form)
        ]

        discount_prices = [p for p in discount_prices if p is not None]
        if discount_prices:
            return min(discount_prices)

    def get_discount_price_for_keys(self, order_form):
        prices = [self.get_discount_price_by_key(k)
                  for k in self._get_applicable_discount_keys(order_form)]
        if prices:
            return min(prices)

    def _get_discount_keys(self):
        if self.discount_prices:
            discount_prices_dict = json.loads(self.discount_prices)
            return list(discount_prices_dict.keys())
        else:
            return []

    def _get_applicable_discount_keys(self, order_form):
        discount_keys = self._get_discount_keys()
        if discount_keys:
            for product_key in order_form.product_keys:
                if discount_keys:
                    order_form_product = order_form.get_product_by_key(product_key)
                    if hasattr(order_form_product, 'discount_keys') and not order_form_product.add.data:
                        affected_keys = set(discount_keys).intersection(order_form_product.discount_keys)
                        for key in affected_keys:
                            discount_keys.remove(key)
        return discount_keys

    def get_discount_price_for_person(self, product_form, order_form, name=None):
        if self.discount_persons:
            if not name:
                name = order_form.name.data
            name_key = name.strip().lower()
            discount_persons = discount_users[self.discount_persons]
            if name_key in discount_persons.keys():
                return discount_persons[name_key]

    def get_discount_price_for_amount(self, product_model, product_form, order_form):
        if self.discount_amounts:
            total_paid = get_total_paid(product_model)
            discount_amounts = json.loads(self.discount_amounts)
            applicable_keys = [int(amount_key) for amount_key in discount_amounts.keys() if total_paid<int(amount_key)]
            if applicable_keys:
                return discount_amounts[str(min(applicable_keys))]



class WorkshopProductMixin:
    workshop_date = None
    workshop_time = None
    workshop_level = None
    workshop_price = None
    workshop_duration = None
    workshop_location = None
    workshop_teachers = None


class ContestProductMixin:
    contest_date = None
    contest_time = None
    contest_level = None
    contest_price = None
    contest_prize = None
    contest_location = None
    contest_format = None


WaitingListsStats = namedtuple('WaitingListsStats', ['leads', 'follows', 'couples'])
WorkshopRegStats = namedtuple('WorkshopRegStats', ['accepted', 'waiting'])


class StrictlyContest(ContestProductMixin, BaseProduct):
    partner_name = None
    partner_email = None

    def get_form(self, product_model=None):
        class StrictlyContestForm(NoCsrfForm):
            product_name = self.name
            product_id = product_model.id
            info = self.info
            price = self.price
            add = BooleanField(label='Book with partner')
            product_type = self.__class__.__name__
            contest_date = self.contest_date
            contest_time = self.contest_time
            contest_level = self.contest_level
            contest_price = self.contest_price
            contest_prize = self.contest_prize
            contest_location = self.contest_location
            contest_format = self.contest_format
            available_quantity = self.get_available_quantity(product_model)
            waiting_lists = self.get_waiting_lists(product_model)

            def needs_partner(self):
                if self.add.data:
                    return True

        return StrictlyContestForm

    def get_total_price(self, product_model, product_form, order_form):
        if product_form.add.data:
            return self.price
        else:
            return 0

    def get_name(self, order_product_model=None):
        if not order_product_model:
            return self.name
        else:
            name1 = order_product_model.registrations[0].name
            name2 = order_product_model.details_as_dict['partner_name']
            return '{} ({} + {})'.format(self.name, name1, name2)

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_model, product_form, form)
        partner_name = form.partner_name.data
        partner_email = form.partner_email.data
        ws = self.get_waiting_lists(product_model)
        status = ORDER_PRODUCT_STATUS_WAITING if ws else ORDER_PRODUCT_STATUS_ACCEPTED
        order_product = OrderProduct(product_model, price, status=status,
                                     details_dict={'partner_name':partner_name, 'partner_email':partner_email})
        return order_product

    @staticmethod
    def get_registration_stats(product_model):
        query = OrderProduct.query.filter_by(product_id=product_model.id). \
            join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID)
        couples_accepted = len(
            query.filter_by(status=ORDER_PRODUCT_STATUS_ACCEPTED).all()
        )
        couples_waiting = len(
            query.filter_by(status=ORDER_PRODUCT_STATUS_WAITING).all()
        )
        return WorkshopRegStats(couples_accepted, couples_waiting)

    @classmethod
    def get_waiting_lists(cls, product_model):
        registration_stats = cls.get_registration_stats(product_model)
        if registration_stats.waiting > 0:
            return registration_stats.waiting + 1
        if registration_stats.accepted + 1 > product_model.max_available:
            return 1
        else:
            return 0

    @classmethod
    def get_available_quantity(cls, product_model):
        reg_stats = cls.get_registration_stats(product_model)
        return product_model.max_available - reg_stats.accepted

    @classmethod
    def can_balance_waiting_list_one_couple(cls, product_model):
        # TODO: this actually doesn't balance anything yet
        return False

class WORKSHOP_OPTIONS:
    LEADER = DANCE_ROLE_LEADER
    FOLLOWER = DANCE_ROLE_FOLLOWER
    COUPLE = 'couple'
    NONE = ''


class RegularPartnerWorkshop(ProductDiscountPricesMixin, WorkshopProductMixin, BaseProduct):
    ratio = None
    allow_first = 0

    def get_form(self, product_model=None):

        waiting_lists0 = self.get_waiting_lists(product_model)
        waiting_lists0[0]['couple'] = waiting_lists0[1][DANCE_ROLE_LEADER] + waiting_lists0[1][DANCE_ROLE_FOLLOWER]

        class RegularPartnerWorkshopForm(NoCsrfForm):
            product_name = self.name
            product_id = product_model.id
            info = self.info
            price = self.price
            discount_keys = self._get_discount_keys()
            add = RadioField(label='Add', default=WORKSHOP_OPTIONS.NONE, choices=[
                (WORKSHOP_OPTIONS.LEADER, 'Leader'),
                (WORKSHOP_OPTIONS.FOLLOWER, 'Follower'),
                (WORKSHOP_OPTIONS.COUPLE, 'Couple'),
                (WORKSHOP_OPTIONS.NONE, 'None')
            ])
            # add = BooleanField(label='Book for yourself')
            # dance_role = SelectField(label='Your role',
            #                          choices=[(DANCE_ROLE_FOLLOWER, 'Follower'), (DANCE_ROLE_LEADER, 'Leader')])
            # add_partner = BooleanField(label='Book for partner')
            partner_token = StringField(label='Partner\'s registration token', validators=[PartnerTokenValid()])
            product_type = self.__class__.__name__
            workshop_date = self.workshop_date
            workshop_time = self.workshop_time
            workshop_location = self.workshop_location
            workshop_level = self.workshop_level
            workshop_price = self.workshop_price
            workshop_teachers = self.workshop_teachers
            waiting_lists = waiting_lists0
            available_quantity = self.get_available_quantity(product_model)
            keywords = self.keywords

            def needs_partner(self):
                return self.add.data == WORKSHOP_OPTIONS.COUPLE

        return RegularPartnerWorkshopForm

    def get_total_price(self, product_model, product_form, order_form, name=None):
        if product_form.add.data:
            discount_price = self.get_discount_price(product_model, product_form, order_form, name)
            if discount_price:
                return discount_price
            else:
                return self.price
        else:
            return 0

    def is_selected(self, product_form):
        return product_form.add.data in (WORKSHOP_OPTIONS.LEADER, WORKSHOP_OPTIONS.FOLLOWER, WORKSHOP_OPTIONS.COUPLE)

    def _get_buyer_role(self, product_form, form):
        if product_form.add.data == WORKSHOP_OPTIONS.COUPLE:
            if form.dance_role:
                return form.dance_role.data
            else:
                return DANCE_ROLE_LEADER
        elif product_form.add.data in (DANCE_ROLE_LEADER, DANCE_ROLE_FOLLOWER):
            return product_form.add.data
        else:
            raise Exception(f'Unknown dance role for choice {product_form.add.data}')

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_model, product_form, form)
        ws = self.get_waiting_lists(product_model)
        dance_role = self._get_buyer_role(product_form, form)

        if product_form.add.data == WORKSHOP_OPTIONS.COUPLE or product_form.partner_token.data:
            status = ORDER_PRODUCT_STATUS_WAITING if ws[1][dance_role] else ORDER_PRODUCT_STATUS_ACCEPTED
        else:
            status = ORDER_PRODUCT_STATUS_WAITING if ws[0][dance_role] else ORDER_PRODUCT_STATUS_ACCEPTED

        order_product = OrderProduct(
            product_model,
            price,
            dict(dance_role=dance_role),
            status=status
        )

        # register partner
        if product_form.add.data == WORKSHOP_OPTIONS.COUPLE:
            partner_name = form.partner_name.data
            price2 = self.get_total_price(product_model, product_form, form, partner_name)
            dance_role2 = flip_role(dance_role)
            status2 = ORDER_PRODUCT_STATUS_WAITING if ws[1][dance_role2] else ORDER_PRODUCT_STATUS_ACCEPTED
            order_product2 = OrderProduct(product_model, price2,
                                         dict(dance_role=dance_role2), status=status2)

            return [order_product, order_product2]
        return order_product

    def get_name(self, order_product_model=None):
        if not order_product_model:
            return self.name
        else:
            name = order_product_model.registrations[0].name
            role = order_product_model.details_as_dict['dance_role']
            # name2 = order_product_model.registrations[1].name
            if name:
                return '{} ({} / {})'.format(self.name, name, role)
            else:
                return '{} ({})'.format(self.name, role)


    @staticmethod
    def get_registration_stats(product_model):
        query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_ACCEPTED). \
            join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID)
        leads_accepted = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_LEADER)
                .all()
        )
        follows_accepted = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_FOLLOWER)
                .all()
        )

        query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_WAITING). \
            join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID)
        leads_waiting = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_LEADER)
                .all()
        )
        follows_waiting = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_FOLLOWER)
                .all()
        )
        return {
            DANCE_ROLE_LEADER: WorkshopRegStats(accepted=leads_accepted, waiting=leads_waiting),
            DANCE_ROLE_FOLLOWER: WorkshopRegStats(accepted=follows_accepted, waiting=follows_waiting)
        }

    @staticmethod
    def get_partner_registration_stats(product_model):
        query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_ACCEPTED). \
            join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID). \
            join(group_order_product_mapping).join(SignupGroup, aliased=True).filter_by(type=SIGNUP_GROUP_PARTNERS)
        leads_accepted = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_LEADER)
                .all()
        )
        follows_accepted = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_FOLLOWER)
                .all()
        )

        query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_WAITING). \
            join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID). \
            join(group_order_product_mapping).join(SignupGroup, aliased=True).filter_by(type=SIGNUP_GROUP_PARTNERS)
        leads_waiting = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_LEADER)
                .all()
        )
        follows_waiting = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_FOLLOWER)
                .all()
        )
        return {
            DANCE_ROLE_LEADER: WorkshopRegStats(accepted=leads_accepted, waiting=leads_waiting),
            DANCE_ROLE_FOLLOWER: WorkshopRegStats(accepted=follows_accepted, waiting=follows_waiting)
        }

    @classmethod
    def get_waiting_lists(cls, product_model):
        reg_stats = cls.get_registration_stats(product_model)
        ratio = float(product_model.parameters_as_dict['ratio'])
        allow_first = int(product_model.parameters_as_dict['allow_first'])
        solo_leads_waiting = cls.get_waiting_list_for_role(
            reg_stats[DANCE_ROLE_LEADER].accepted,
            reg_stats[DANCE_ROLE_LEADER].waiting,
            reg_stats[DANCE_ROLE_FOLLOWER].accepted,
            product_model.max_available, ratio, allow_first
        )
        solo_follows_waiting = cls.get_waiting_list_for_role(
            reg_stats[DANCE_ROLE_FOLLOWER].accepted,
            reg_stats[DANCE_ROLE_FOLLOWER].waiting,
            reg_stats[DANCE_ROLE_LEADER].accepted,
            product_model.max_available, ratio, allow_first
        )
        ws_solo = {
            DANCE_ROLE_LEADER: solo_leads_waiting,
            DANCE_ROLE_FOLLOWER: solo_follows_waiting
        }
        total_accepted = reg_stats[DANCE_ROLE_LEADER].accepted + reg_stats[DANCE_ROLE_FOLLOWER].accepted

        max_ratio = 2
        partner_reg_stats = cls.get_partner_registration_stats(product_model)

        partner_leads_waiting = cls.get_waiting_list_for_role(
            reg_stats[DANCE_ROLE_LEADER].accepted,
            partner_reg_stats[DANCE_ROLE_LEADER].waiting,
            reg_stats[DANCE_ROLE_FOLLOWER].accepted,
            product_model.max_available, max_ratio, allow_first
        )

        partner_follows_waiting = cls.get_waiting_list_for_role(
            reg_stats[DANCE_ROLE_FOLLOWER].accepted,
            partner_reg_stats[DANCE_ROLE_FOLLOWER].waiting,
            reg_stats[DANCE_ROLE_LEADER].accepted,
            product_model.max_available, max_ratio, allow_first
        )

        if product_model.max_available - total_accepted == 1:
            if reg_stats[DANCE_ROLE_FOLLOWER].accepted > reg_stats[DANCE_ROLE_LEADER].accepted:
                partner_leads_waiting += 1
            else:
                partner_follows_waiting += 1

        ws_with_couple = {
            DANCE_ROLE_LEADER: partner_leads_waiting,
            DANCE_ROLE_FOLLOWER: partner_follows_waiting
        }

        return ws_solo, ws_with_couple

    @classmethod
    def get_available_quantity(cls, product_model):
        reg_stats = cls.get_registration_stats(product_model)
        available_quantity = product_model.max_available \
                             - reg_stats[DANCE_ROLE_LEADER].accepted \
                             - reg_stats[DANCE_ROLE_FOLLOWER].accepted
        return available_quantity

    @staticmethod
    def get_waiting_list_for_role(accepted, waiting, accepted_other, max_available, ratio, allow_first):
        if waiting > 0:
            return waiting + 1
        elif accepted + accepted_other + 1 > max_available:
            return 1
        elif accepted + 1 < allow_first:
            return 0
        elif accepted + 1 > accepted_other * ratio:
            return 1
        else:
            return 0

    @classmethod
    def can_balance_waiting_list_one(cls, product_model):
        reg_stats = cls.get_registration_stats(product_model)
        ratio = float(product_model.parameters_as_dict['ratio'])
        max_ratio = 2
        # both waiting lists empty => None
        if reg_stats[DANCE_ROLE_LEADER].waiting == 0 and reg_stats[DANCE_ROLE_FOLLOWER].waiting == 0:
            return False
        # no available places => None
        elif reg_stats[DANCE_ROLE_LEADER].accepted + reg_stats[DANCE_ROLE_FOLLOWER].accepted >= product_model.max_available:
            return False
        # both waiting lists not empty
        elif reg_stats[DANCE_ROLE_LEADER].waiting > 0 and reg_stats[DANCE_ROLE_FOLLOWER].waiting > 0:
            # adding leader will imbalance event => follower
            if reg_stats[DANCE_ROLE_LEADER].accepted + 1.0 >= reg_stats[DANCE_ROLE_FOLLOWER].accepted * ratio:
                return DANCE_ROLE_FOLLOWER
            # adding follower will imbalance event => leader
            elif reg_stats[DANCE_ROLE_FOLLOWER].accepted + 1.0 >= reg_stats[DANCE_ROLE_LEADER].accepted * ratio:
                return DANCE_ROLE_LEADER
            else:
                return True
        # only followers waiting list
        elif reg_stats[DANCE_ROLE_FOLLOWER].waiting > 0:
            # adding follower will not imbalance event => follower
            if reg_stats[DANCE_ROLE_FOLLOWER].accepted + 1.0 <= reg_stats[DANCE_ROLE_LEADER].accepted * ratio:
                return DANCE_ROLE_FOLLOWER
            else:
                return False
        # only leads waiting list
        elif reg_stats[DANCE_ROLE_LEADER].waiting > 0:
            # adding leader will not imbalance event => follower
            if reg_stats[DANCE_ROLE_LEADER].accepted + 1.0 <= reg_stats[DANCE_ROLE_FOLLOWER].accepted * ratio:
                return DANCE_ROLE_LEADER
            else:
                return False
        else:
            return False

    @classmethod
    def balance_waiting_list(cls, product_model):
        can_balance = cls.can_balance_waiting_list_one(product_model)
        results = []
        while can_balance:
            # get top waiting with partners
            query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_WAITING). \
                join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID). \
                join(group_order_product_mapping).join(SignupGroup, aliased=True).filter_by(type=SIGNUP_GROUP_PARTNERS)
            if can_balance in (DANCE_ROLE_FOLLOWER, DANCE_ROLE_LEADER):
                query = query.join(OrderProductDetail, aliased=True).filter_by(field_name='dance_role',
                                                                               field_value=can_balance)
            order_product = query.join(Order).order_by(asc(Order.order_datetime)).first()
            if order_product:
                cls.accept_from_waiting_list(order_product)
                results.append(order_product)
            else:
                # get top waiting (without partners)
                query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_WAITING). \
                    join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID)
                if can_balance in (DANCE_ROLE_FOLLOWER, DANCE_ROLE_LEADER):
                    query = query.join(OrderProductDetail, aliased=True).filter_by(field_name='dance_role', field_value=can_balance)
                order_product = query.join(Order).order_by(asc(Order.order_datetime)).first()
                if order_product:
                    cls.accept_from_waiting_list(order_product)
                    results.append(order_product)
            can_balance = cls.can_balance_waiting_list_one(product_model)
        return results

    @classmethod
    def accept_from_waiting_list(cls, order_product):
        order_product.status = ORDER_PRODUCT_STATUS_ACCEPTED
        db_session.commit()


class CouplesOnlyWorkshop(ProductDiscountPricesMixin, WorkshopProductMixin, BaseProduct):

    def get_form(self, product_model=None):
        class CouplesContestForm(NoCsrfForm):
            product_name = self.name
            product_id = product_model.id
            info = self.info
            price = self.price
            discount_keys = self._get_discount_keys()
            add = BooleanField(label='Book for yourself')
            dance_role = SelectField(label='Your role',
                                     choices=[(DANCE_ROLE_FOLLOWER, 'Follower'), (DANCE_ROLE_LEADER, 'Leader')])
            add_partner = BooleanField(label='Book for partner')
            partner_token = StringField(label='Partner\'s registration token', validators=[PartnerTokenValid()])
            product_type = self.__class__.__name__
            workshop_date = self.workshop_date
            workshop_time = self.workshop_time
            workshop_location = self.workshop_location
            workshop_level = self.workshop_level
            workshop_price = self.workshop_price
            waiting_lists = self.get_waiting_lists(product_model)
            available_quantity = self.get_available_quantity(product_model)

            def needs_partner(self):
                if self.add_partner.data:
                    return True
                else:
                    return False

        return CouplesContestForm

    def get_total_price(self, product_model, product_form, order_form):
        if product_form.add.data:
            discount_price = self.get_discount_price(product_model, product_form, order_form)
            if discount_price:
                return discount_price
            else:
                return self.price
        else:
            return 0

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_model, product_form, form)
        ws = self.get_waiting_lists(product_model)
        dance_role = product_form.dance_role.data

        if product_form.add_partner.data or product_form.partner_token.data:
            status = ORDER_PRODUCT_STATUS_WAITING if ws else ORDER_PRODUCT_STATUS_ACCEPTED
        else:
            status = ORDER_PRODUCT_STATUS_WAITING

        order_product = OrderProduct(
            product_model,
            price,
            dict(dance_role=dance_role),
            status=status
        )

        # register partner
        if product_form.add_partner.data:
            dance_role = flip_role(dance_role)
            status = ORDER_PRODUCT_STATUS_WAITING if ws else ORDER_PRODUCT_STATUS_ACCEPTED
            order_product2 = OrderProduct(product_model, price,
                                         dict(dance_role=dance_role), status=status)

            return [order_product, order_product2]
        return order_product

    def get_name(self, order_product_model=None):
        if not order_product_model:
            return self.name
        else:
            name = order_product_model.registrations[0].name
            role = order_product_model.details_as_dict['dance_role']
            # name2 = order_product_model.registrations[1].name
            return '{} ({} / {})'.format(self.name, name, role)

    @staticmethod
    def get_registration_stats(product_model):
        query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_ACCEPTED). \
            join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID)
        leads_accepted = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_LEADER)
                .all()
        )
        follows_accepted = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_FOLLOWER)
                .all()
        )

        query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_WAITING). \
            join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID)
        leads_waiting = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_LEADER)
                .all()
        )
        follows_waiting = len(
            query.join(aliased(OrderProductDetail))
                .filter_by(field_name='dance_role', field_value=DANCE_ROLE_FOLLOWER)
                .all()
        )
        return {
            DANCE_ROLE_LEADER: WorkshopRegStats(accepted=leads_accepted, waiting=leads_waiting),
            DANCE_ROLE_FOLLOWER: WorkshopRegStats(accepted=follows_accepted, waiting=follows_waiting),
        }

    @classmethod
    def get_available_quantity(cls, product_model):
        reg_stats = cls.get_registration_stats(product_model)
        available_quantity = product_model.max_available \
                             - reg_stats[DANCE_ROLE_LEADER].accepted \
                             - reg_stats[DANCE_ROLE_FOLLOWER].accepted
        return available_quantity

    @classmethod
    def get_waiting_lists(cls, product_model):
        reg_stats = cls.get_registration_stats(product_model)
        if reg_stats[DANCE_ROLE_FOLLOWER].accepted + reg_stats[DANCE_ROLE_LEADER].accepted + 2 > product_model.max_available:
            return 1
        else:
            return 0

    @classmethod
    def can_balance_waiting_list_one_couple(cls, product_model):
        # TODO: this actually doesn't balance anything yet
        reg_stats = cls.get_registration_stats(product_model)
        # both waiting lists empty => None
        if reg_stats[DANCE_ROLE_LEADER].waiting == 0 and reg_stats[DANCE_ROLE_FOLLOWER].waiting == 0:
            return False
        # no available places => None
        elif reg_stats[DANCE_ROLE_LEADER].accepted + reg_stats[DANCE_ROLE_FOLLOWER].accepted + 2 > product_model.max_available:
            return False
        else:
            return False

    @classmethod
    def balance_waiting_list(cls, product_model):
        can_balance = cls.can_balance_waiting_list_one_couple(product_model)
        results = []
        while can_balance:
            # get top waiting with partners
            query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_WAITING). \
                join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID). \
                join(group_order_product_mapping).join(SignupGroup, aliased=True).filter_by(type=SIGNUP_GROUP_PARTNERS)
            if can_balance in (DANCE_ROLE_FOLLOWER, DANCE_ROLE_LEADER):
                query = query.join(OrderProductDetail, aliased=True).filter_by(field_name='dance_role',
                                                                               field_value=can_balance)
            order_product = query.join(Order).order_by(asc(Order.order_datetime)).first()
            if order_product:
                group = SignupGroup.join(group_order_product_mapping).\
                    join(OrderProduct, aliased=True).filter_by(type=SIGNUP_GROUP_PARTNERS, id=order_product.id).\
                    first()
                for partners_order_product in group.order_products:
                    cls.accept_from_waiting_list(partners_order_product)
                    results.append(partners_order_product)
            can_balance = cls.can_balance_waiting_list_one_couple(product_model)
        return results

    @classmethod
    def accept_from_waiting_list(cls, order_product):
        order_product.status = ORDER_PRODUCT_STATUS_ACCEPTED
        db_session.commit()


class MarketingProduct(BaseProduct):
    allow_select = None
    img_src = None

    def get_form(self, product_model=None):
        class MarketingProductForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            img_src = self.img_src
            price = self.price
            available_quantity = self.get_available_quantity(product_model)
            product_type = self.__class__.__name__

            def needs_partner(self):
                return False

        if self.allow_select:
            quantity = min(self.get_available_quantity(product_model), int(self.allow_select))
        else:
            quantity = self.get_available_quantity(product_model)

        setattr(
            MarketingProductForm,
            'add',
            SelectField(label='Add', choices=[(str(x), str(x)) for x in range(0, quantity+1)], validators=[Optional()])
        )
        return MarketingProductForm

    def get_available_quantity(self, product_model):
        assert isinstance(product_model, Product)
        ordered_quantity = OrderProduct.query.filter(OrderProduct.product == product_model).count()
        return max(self.max_available - ordered_quantity, 0)

    def get_total_price(self, product_model, product_form, order_form=None):
        if product_form.add.data:
            return self.price
        else:
            return 0


class DonateProduct(BaseProduct):
    make_public = True

    def get_form(self, product_model=None):
        class DonateForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            product_type = self.__class__.__name__
            amount = FloatField(label='Amount', validators=[Optional()])

            def needs_partner(self):
                return False

        return DonateForm

    def get_total_price(self, product_model, product_form, order_form=None):
        if product_form.amount.data:
            return float(product_form.amount.data)
        else:
            return 0

class FESTIVAL_TICKET:
    SINGLE = 'single'
    COUPLE = 'couple'
    NONE = ''

class FestivalTicketProduct(BaseProduct):
    def get_form(self, product_model=None):
        class FestivalTrackForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            price = self.price
            keywords = self.keywords
            product_id = product_model.id
            product_type = self.__class__.__name__
            amount = FloatField(label='Amount', validators=[Optional()])
            add = RadioField(label='Add', choices=[
                (FESTIVAL_TICKET.SINGLE, 'One Ticket'),
                (FESTIVAL_TICKET.COUPLE, 'Two Tickets'),
                (FESTIVAL_TICKET.NONE, 'None')
            ])

            def needs_partner(self):
                return self.add.data == FESTIVAL_TICKET.COUPLE

        return FestivalTrackForm

    def get_total_price(self, product_model, product_form, order_form=None):
        if product_form.add.data in (FESTIVAL_TICKET.SINGLE, FESTIVAL_TICKET.COUPLE):
            return float(self.price)
        else:
            return 0

    def is_selected(self, product_form):
        return product_form.add.data in (FESTIVAL_TICKET.SINGLE, FESTIVAL_TICKET.COUPLE)

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_model, product_form, form)
        order_product = OrderProduct(product_model, price, status=ORDER_PRODUCT_STATUS_ACCEPTED)

        # register partner
        if product_form.add.data == FESTIVAL_TICKET.COUPLE:
            partner_name = form.partner_name.data
            price2 = self.get_total_price(product_model, product_form, form)
            order_product2 = OrderProduct(product_model, price2, status=ORDER_PRODUCT_STATUS_ACCEPTED)
            return [order_product, order_product2]

        return order_product

    def get_name(self, order_product_model=None):
        if not order_product_model:
            return self.name
        else:
            name = order_product_model.registrations[0].name
            # name2 = order_product_model.registrations[1].name
            if name:
                return '{} ({})'.format(self.name, name)
            else:
                return '{}'.format(self.name)



class FestivalTrackProduct(FestivalTicketProduct):
    classes_to_chose = None
    includes = None

    def get_form(self, product_model=None):
        form = super(FestivalTrackProduct, self).get_form(product_model=product_model)
        form.includes = self.includes
        return form


class FestivalPartyProduct(FestivalTicketProduct):
    party_date = None
    party_time = None
    party_location = None

    def get_form(self, product_model=None):
        form = super(FestivalPartyProduct, self).get_form(product_model=product_model)
        form.party_date = self.party_date
        return form


class FestivalGroupDiscountProduct(BaseProduct):
    includes = None
    def get_form(self, product_model=None):
        class FestivalGroupDiscountForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            product_id = product_model.id
            keywords = self.keywords
            product_type = self.__class__.__name__
            add = StringField('Group Name')
            location = StringField('Group Location')
            location = TextField('Group Description')

            def needs_partner(self):
                return False

        return FestivalGroupDiscountForm

    def get_total_price(self, product_model, product_form, order_form=None):
        if order_form:
            ticket_form = self._get_selected_included_product_form(order_form)
            if ticket_form:
                return -float(self.price)
        return 0

    def is_selected(self, product_form):
        return product_form.add.data and product_form.add.data.strip()

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_model, product_form, form)
        order_product = OrderProduct(product_model, price, status=ORDER_PRODUCT_STATUS_ACCEPTED)

        # register partner
        ticket_form = self._get_selected_included_product_form(form)
        if ticket_form and ticket_form.add.data == FESTIVAL_TICKET.COUPLE:
            order_product2 = OrderProduct(product_model, price, status=ORDER_PRODUCT_STATUS_ACCEPTED)
            return [order_product, order_product2]

        return order_product

    def get_name(self, order_product_model=None):
        if not order_product_model:
            return self.name
        else:
            name = order_product_model.registrations[0].name
            # name2 = order_product_model.registrations[1].name
            if name:
                return '{} ({})'.format(self.name, name)
            else:
                return '{}'.format(self.name)

    def _get_selected_included_product_form(self, form):
        includes_keywords = self.includes.split(',')
        for product_key in form.product_keys:
            product_form = form.get_product_by_key(product_key)
            if product_form.add.data:
                if product_form.keywords and set(product_form.keywords.split(',')).intersection(includes_keywords):
                    return product_form

    @staticmethod
    def convert_group_name(name):
        return name.strip().lower()

    def retrieve_group_details(self, name, event):
        group = RegistrationGroup.query.filter_by(name=self.convert_group_name(name), event_id=event.id).one_or_none()
        return group

    def create_new_group(self, group_form, event):
        pass
        event.registration_groups.append()

# def get_class_by_name(class_name):
#     import sys
#     import inspect
#     current_module = sys.modules[__name__]
#     class_obj = dict(inspect.getmembers(current_module))[class_name]
#     return class_obj
#
#
# def get_product_by_model_old(db_model):
#     assert (isinstance(db_model, Product))
#     class_name = db_model.type
#     product_class = get_class_by_name(class_name)
#     assert issubclass(product_class, ProductTemplate)
#     return product_class.from_model(db_model)

product_mapping = {
    'RegularPartnerWorkshop': RegularPartnerWorkshop,
    'CouplesOnlyWorkshop': CouplesOnlyWorkshop,
    'MarketingProduct': MarketingProduct,
    'DonateProduct': DonateProduct,
    'StrictlyContest': StrictlyContest,
    'FestivalTrackProduct': FestivalTrackProduct,
    'FestivalPartyProduct': FestivalPartyProduct,
    'FestivalGroupDiscountProduct': FestivalGroupDiscountProduct,
}


def get_product_by_model(db_model):
    assert (isinstance(db_model, Product))
    class_name = db_model.type
    product_class = product_mapping[class_name]
    assert issubclass(product_class, BaseProduct)
    return product_class.from_model(db_model)


class PartnerTokenValid:
    def __call__(self, form, field):
        if field.data:
            try:
                partner_product_order = order_product_deserialize(field.data)
            except BadSignature:
                raise ValidationError('Invalid token')

            if form.product_id != partner_product_order.product.id:
                raise ValidationError('The token is for a different workshop')

            if form.dance_role.data == partner_product_order.details_as_dict['dance_role']:
                raise ValidationError('Partner has the same role')

            if partner_product_order.status != ORDER_PRODUCT_STATUS_WAITING and order_product_token_expired(field.data, 60*60*24):
                raise ValidationError('Token has expired')

            has_partners = (len(SignupGroup.query.
                                join(group_order_product_mapping).
                                join(OrderProduct).filter_by(id=partner_product_order.id).all()) > 0)
            if has_partners:
                raise ValidationError('Your partner has already signed up with a partner')




