from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, DateTimeField, SubmitField, SelectField, BooleanField, FormField, FieldList, HiddenField
from .models import Product, ProductParameter


class ProductTemplate:
    name = ''
    info = ''
    parameters = {}

    def __init__(self, name, info=None, parameters_dict=None):
        self.name = name
        if info:
            self.info = info
        if parameters_dict:
            self.parameters = parameters_dict

    def get_form(self):
        raise NotImplementedError()

    @property
    def model(self):
        return Product(self.name, self.__class__.__name__, info=self.info, parameters_dict=self.parameters)

    @classmethod
    def from_model(cls, db_model):
        assert (isinstance(db_model, Product))
        product = cls(db_model.name)
        if db_model.info:
            product.info = db_model.info
        # TODO: parameters
        return product


class CouplesOnlyWorkshop(ProductTemplate):
    def get_form(self):
        class CouplesOnlyWorkshopForm(NoCsrfForm):
            info = self.info
            price = 50
            going = BooleanField(label=self.name)
            partner_name = StringField('Your partner name')
        return CouplesOnlyWorkshopForm


class RegularPartnerWorkshop(ProductTemplate):
    def get_form(self):
        class RegularPartnerWorkshopForm(NoCsrfForm):
            info = self.info
            price = 50
            going = BooleanField(label=self.name)
            dance_role = SelectField(label='Your role',
                                     choices=[('follower', 'Follower'), ('leader', 'Leader')])
        return RegularPartnerWorkshopForm


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
}


def get_product_by_model(db_model):
    assert (isinstance(db_model, Product))
    class_name = db_model.type
    product_class = product_mapping[class_name]
    assert issubclass(product_class, ProductTemplate)
    return product_class.from_model(db_model)
