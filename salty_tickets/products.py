import inspect
from collections import namedtuple

import math

from salty_tickets.database import db_session
from sqlalchemy import asc
from sqlalchemy.orm import aliased
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, HiddenField, IntegerField, FloatField
from wtforms.validators import Optional

from salty_tickets.models import Product, ProductParameter, OrderProduct, DANCE_ROLE_FOLLOWER, DANCE_ROLE_LEADER, Order, \
    ORDER_STATUS_PAID, OrderProductDetail, ORDER_PRODUCT_STATUS_ACCEPTED, ORDER_PRODUCT_STATUS_WAITING, Registration
import json


def flip_role(dance_role):
    if dance_role == DANCE_ROLE_FOLLOWER:
        return DANCE_ROLE_LEADER
    else:
        return DANCE_ROLE_FOLLOWER


class ProductTemplate:
    name = ''
    info = ''
    max_available = 0
    price = None
    image_url = None
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

    def get_ordered_product_model(self, product_form):
        order_product_model = OrderProduct(price=product_form.price)

    @property
    def _parameters_dict(self):
        cls = type(self)
        attrs = inspect.getmembers(cls, lambda a: not (inspect.ismethod(a) or inspect.isfunction(a) or isinstance(a, property)))
        attrs = [a[0] for a in attrs if not(a[0].startswith('_') or a[0].endswith('_'))
                                     and not a[0] in self._basic_attrs]
        params_dict = {a: getattr(self, a) for a in attrs}
        return params_dict

    def get_total_price(self, produc_form, form):
        raise NotImplementedError()

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_form, form)
        status =  ORDER_PRODUCT_STATUS_ACCEPTED
        order_product = OrderProduct(product_model, price, status=status)
        return order_product


class ProductDiscountPrices:
    discount_prices = None

    def get_discount_price_by_key(self, key):
        discount_prices_dict = json.loads(self.discount_prices)
        return discount_prices_dict[key]

    def get_discount_price(self, product_form, order_form):
        prices = [self.get_discount_price_by_key(k)
                  for k in self._get_applicable_discount_keys(product_form, order_form)]
        if prices:
            return min(prices)

    def _get_discount_keys(self):
        discount_prices_dict = json.loads(self.discount_prices)
        return list(discount_prices_dict.keys())

    def _get_applicable_discount_keys(self, product_form, order_form):
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



class WorkshopProduct:
    workshop_date = None
    workshop_time = None
    workshop_level = None
    workshop_price = None
    workshop_duration = None


WaitingListsStats = namedtuple('WaitingListsStats', ['leads', 'follows', 'couples'])
WorkshopRegStats = namedtuple('WorkshopRegStats', ['accepted', 'waiting'])


class CouplesOnlyWorkshop(ProductTemplate, ProductDiscountPrices, WorkshopProduct):

    def get_form(self, product_model=None):
        class CouplesOnlyWorkshopForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            price = self.price
            discount_keys = self._get_discount_keys()
            add = BooleanField(label='Book with partner')
            partner_name = StringField('Your partner name')
            product_type = self.__class__.__name__
            workshop_date = self.workshop_date
            workshop_time = self.workshop_time
            workshop_level = self.workshop_level
            workshop_price = self.workshop_price
            waiting_list = self.get_waiting_lists(product_model)

            def needs_partner(self):
                return self.add.data

        return CouplesOnlyWorkshopForm

    def get_total_price(self, product_form, order_form):
        if product_form.add.data:
            discount_price = self.get_discount_price(product_form, order_form)
            if discount_price:
                return discount_price
            else:
                return self.price
        else:
            return 0

    def get_name(self, order_product_model=None):
        if not order_product_model:
            return self.name
        else:
            name1 = order_product_model.registrations[0].name
            name2 = order_product_model.registrations[1].name
            return '{} ({} + {})'.format(self.name, name1, name2)

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_form, form)
        ws = self.get_waiting_lists(product_model)
        status = ORDER_PRODUCT_STATUS_WAITING if ws else ORDER_PRODUCT_STATUS_ACCEPTED
        order_product = OrderProduct(product_model, price, status=status)
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
        print(registration_stats)
        if registration_stats.waiting > 0:
            return registration_stats.waiting + 1
        if registration_stats.accepted + 1 > product_model.max_available:
            return 1
        else:
            return 0


class RegularPartnerWorkshop(ProductTemplate, WorkshopProduct):
    ratio = None
    allow_first = 0

    def get_form(self, product_model=None):
        class RegularPartnerWorkshopForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            price = self.price
            add = BooleanField(label='Book for yourself')
            dance_role = SelectField(label='Your role',
                                     choices=[(DANCE_ROLE_FOLLOWER, 'Follower'), (DANCE_ROLE_LEADER, 'Leader')])
            add_partner = BooleanField(label='Book for partner')
            partner_token = StringField(label='Partner\'s token')
            product_type = self.__class__.__name__
            workshop_date = self.workshop_date
            workshop_time = self.workshop_time
            workshop_level = self.workshop_level
            workshop_price = self.workshop_price
            waiting_lists = self.get_waiting_lists(product_model)

            def needs_partner(self):
                if self.add_partner.data:
                    return True
                else:
                    return False

        return RegularPartnerWorkshopForm

    def get_total_price(self, product_form, order_form=None):
        if product_form.add.data:
            return self.price
        else:
            return 0

    def get_order_product_model(self, product_model, product_form, form):
        price = self.get_total_price(product_form, form)
        ws = self.get_waiting_lists(product_model)
        dance_role = product_form.dance_role.data

        if product_form.add_partner.data:
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
        if product_form.add_partner.data:
            dance_role = flip_role(dance_role)
            status = ORDER_PRODUCT_STATUS_WAITING if ws[1][dance_role] else ORDER_PRODUCT_STATUS_ACCEPTED
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
            DANCE_ROLE_FOLLOWER: WorkshopRegStats(accepted=follows_accepted, waiting=follows_waiting)
        }

    @classmethod
    def get_waiting_lists(cls, product_model):
        registration_stats = cls.get_registration_stats(product_model)
        print(registration_stats)
        ratio = float(product_model.parameters_as_dict['ratio'])
        allow_first = int(product_model.parameters_as_dict['allow_first'])
        solo_leads_waiting = cls.get_waiting_list_for_role(
            registration_stats[DANCE_ROLE_LEADER].accepted,
            registration_stats[DANCE_ROLE_LEADER].waiting,
            registration_stats[DANCE_ROLE_FOLLOWER].accepted,
            product_model.max_available, ratio, allow_first
        )
        solo_follows_waiting = cls.get_waiting_list_for_role(
            registration_stats[DANCE_ROLE_FOLLOWER].accepted,
            registration_stats[DANCE_ROLE_FOLLOWER].waiting,
            registration_stats[DANCE_ROLE_LEADER].accepted,
            product_model.max_available, ratio, allow_first
        )
        ws_solo = {
            DANCE_ROLE_LEADER: solo_leads_waiting,
            DANCE_ROLE_FOLLOWER: solo_follows_waiting
        }
        total_accepted = registration_stats[DANCE_ROLE_LEADER].accepted + registration_stats[DANCE_ROLE_FOLLOWER].accepted

        if total_accepted + 2 <= product_model.max_available:
            ws_with_couple = {
                DANCE_ROLE_LEADER: 0,
                DANCE_ROLE_FOLLOWER: 0
            }
        elif product_model.max_available - total_accepted == 1:
            ws_with_couple = {
                DANCE_ROLE_LEADER: 1,
                DANCE_ROLE_FOLLOWER: 0
            }
        else:
            ws_with_couple = {
                DANCE_ROLE_LEADER: 1,
                DANCE_ROLE_FOLLOWER: 1
            }

        return ws_solo, ws_with_couple

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
        # both waiting lists empty => None
        if reg_stats[DANCE_ROLE_LEADER].waiting == 0 and reg_stats[DANCE_ROLE_FOLLOWER].waiting == 0:
            return False
        # no available places => None
        elif reg_stats[DANCE_ROLE_LEADER].accepted + reg_stats[DANCE_ROLE_FOLLOWER].accepted >= product_model.max_available:
            return False
        # both waiting lists not empty
        elif reg_stats[DANCE_ROLE_LEADER].waiting > 0 and reg_stats[DANCE_ROLE_FOLLOWER].waiting > 0:
            # adding leader will imbalance event => follower
            if reg_stats[DANCE_ROLE_LEADER].accepted + 1 >= reg_stats[DANCE_ROLE_FOLLOWER].accepted * ratio:
                return DANCE_ROLE_FOLLOWER
            # adding follower will imbalance event => leader
            elif reg_stats[DANCE_ROLE_FOLLOWER].accepted + 1 >= reg_stats[DANCE_ROLE_LEADER].accepted * ratio:
                return DANCE_ROLE_LEADER
            else:
                return True
        # only followers waiting list
        elif reg_stats[DANCE_ROLE_FOLLOWER].waiting > 0:
            # adding follower will not imbalance event => follower
            if reg_stats[DANCE_ROLE_FOLLOWER].accepted + 1 <= reg_stats[DANCE_ROLE_LEADER].accepted * ratio:
                return DANCE_ROLE_FOLLOWER
            else:
                return False
        # only leads waiting list
        elif reg_stats[DANCE_ROLE_LEADER].waiting > 0:
            # adding leader will not imbalance event => follower
            if reg_stats[DANCE_ROLE_LEADER].accepted + 1 <= reg_stats[DANCE_ROLE_FOLLOWER].accepted * ratio:
                return DANCE_ROLE_LEADER
            else:
                return False
        else:
            return False

    @classmethod
    def balance_waiting_list(cls, product_model):
        can_balance = cls.can_balance_waiting_list_one(product_model)
        while can_balance:
            # get top waiting
            query = product_model.product_orders.filter_by(status=ORDER_PRODUCT_STATUS_WAITING). \
                join(Order, aliased=True).filter_by(status=ORDER_STATUS_PAID)
            if can_balance in (DANCE_ROLE_FOLLOWER, DANCE_ROLE_LEADER):
                query = query.join(OrderProductDetail, aliased=True).filter_by(field_name='dance_role', field_value=can_balance)
            order_product = query.join(Order).order_by(asc(Order.order_datetime)).first()
            if order_product:
                cls.accept_from_waiting_list(order_product)
            can_balance = cls.can_balance_waiting_list_one(product_model)
        print(cls.get_registration_stats(product_model))

    @classmethod
    def accept_from_waiting_list(cls, order_product):
        print(order_product.registrations[0].name, order_product.registrations[0].registered_datetime, order_product.id, order_product.status, order_product.details_as_dict['dance_role'])
        order_product.status = ORDER_PRODUCT_STATUS_ACCEPTED
        db_session.commit()
        # TODO: user notification when accepted from waiting list
        # TODO: users with partners should have higher priority


class MarketingProduct(ProductTemplate):
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
            SelectField(label='Add', choices=[(str(x), str(x)) for x in range(0, quantity+1)])
        )
        return MarketingProductForm

    def get_available_quantity(self, product_model):
        assert isinstance(product_model, Product)
        ordered_quantity = OrderProduct.query.filter(OrderProduct.product == product_model).count()
        return max(self.max_available - ordered_quantity, 0)

    def get_total_price(self, product_form, order_form=None):
        if product_form.add.data:
            return self.price
        else:
            return 0


class DonateProduct(ProductTemplate):
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

    def get_total_price(self, product_form, order_form=None):
        if product_form.amount.data:
            return float(product_form.amount.data)
        else:
            return 0



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
}


def get_product_by_model(db_model):
    assert (isinstance(db_model, Product))
    class_name = db_model.type
    product_class = product_mapping[class_name]
    assert issubclass(product_class, ProductTemplate)
    return product_class.from_model(db_model)
