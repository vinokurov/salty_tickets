import inspect

from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, HiddenField, IntegerField, FloatField
from wtforms.validators import Optional

from salty_tickets.models import Product, ProductParameter, OrderProduct, DANCE_ROLE_FOLLOWER, DANCE_ROLE_LEADER
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
        order_product = OrderProduct(product_model, price)
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


class CouplesOnlyWorkshop(ProductTemplate, ProductDiscountPrices, WorkshopProduct):

    def get_form(self, product_model=None):
        class CouplesOnlyWorkshopForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            price = self.price
            discount_keys = self._get_discount_keys()
            add = BooleanField(label='Add')
            partner_name = StringField('Your partner name')
            product_type = self.__class__.__name__
            workshop_date = self.workshop_date
            workshop_time = self.workshop_time
            workshop_level = self.workshop_level

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


class RegularPartnerWorkshop(ProductTemplate, WorkshopProduct):
    ratio = None

    def get_form(self, product_model=None):
        class RegularPartnerWorkshopForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            price = self.price
            add = BooleanField(label='Add')
            dance_role = SelectField(label='Your role',
                                     choices=[(DANCE_ROLE_FOLLOWER, 'Follower'), (DANCE_ROLE_LEADER, 'Leader')])
            add_partner = BooleanField(label='Add partner')
            partner_token = StringField(label='Partner\'s token')
            product_type = self.__class__.__name__
            workshop_date = self.workshop_date
            workshop_time = self.workshop_time
            workshop_level = self.workshop_level

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
        order_product = OrderProduct(product_model, price, dict(dance_role=product_form.dance_role.data))
        if product_form.add_partner.data:
            print(product_form.dance_role.data, flip_role(product_form.dance_role.data))
            order_product2 = OrderProduct(product_model, price,
                                         dict(dance_role=flip_role(product_form.dance_role.data)))
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

    def get_total_price(self, form):
        if form.add.data:
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

        return DonateForm

    def get_total_price(self, form):
        if form.amount.data:
            return float(form.amount.data)
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
