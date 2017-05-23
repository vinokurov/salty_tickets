import inspect

from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, HiddenField, IntegerField, FloatField
from wtforms.validators import Optional

from .models import Product, ProductParameter, OrderProduct


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


class CouplesOnlyWorkshop(ProductTemplate):
    price_weekend = None
    weekend_key = None

    def get_form(self):
        class CouplesOnlyWorkshopForm(NoCsrfForm):
            info = self.info
            price = 50
            add = BooleanField(label=self.name)
            partner_name = StringField('Your partner name')
        return CouplesOnlyWorkshopForm


class RegularPartnerWorkshop(ProductTemplate):
    price_weekend = None
    weekend_key = None
    ratio = None

    def get_form(self):
        class RegularPartnerWorkshopForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            price = 50
            add = BooleanField(label=self.name)
            dance_role = SelectField(label='Your role',
                                     choices=[('follower', 'Follower'), ('leader', 'Leader')])
        return RegularPartnerWorkshopForm


class MarketingProduct(ProductTemplate):
    allow_select = None

    def get_form(self):
        class MarketingProductForm(NoCsrfForm):
            product_name = self.name
            info = self.info
            image_url = self.image_url
            price = self.price
            available_quantity = self.available_quantity
            product_type = self.__class__.__name__

        if self.allow_select:
            quantity = min(self.available_quantity, int(self.allow_select))
        else:
            quantity = self.available_quantity

        setattr(
            MarketingProductForm,
            'add',
            SelectField(label='Add', choices=[(str(x), str(x)) for x in range(0, quantity+1)])
        )
        return MarketingProductForm

    @property
    def available_quantity(self):
        # OrderProduct.query()
        return self.max_available

    def get_total_price(self, form):
        if form.add.data:
            return self.price
        else:
            return 0


class DonateProduct(ProductTemplate):
    make_public = True

    def get_form(self):
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
