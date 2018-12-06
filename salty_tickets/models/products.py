import typing

from salty_tickets.models.registrations import Purchase, Person
from salty_tickets.utils.utils import string_to_key
from wtforms import Form as NoCsrfForm
from dataclasses import dataclass, field
from salty_tickets.forms import RawField, get_primary_personal_info_from_form


class ProductForm(NoCsrfForm):
    add = RawField()


@dataclass
class Product:
    name: str
    key: str = None
    info: str = None
    max_available: int = None
    base_price: float = 0
    image_urls: typing.List = field(default_factory=list)
    tags: typing.Set = field(default_factory=set)
    options: typing.Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.key is None:
            self.key = string_to_key(self.name)

    @classmethod
    def get_form_class(cls):
        return ProductForm

    @classmethod
    def is_added(cls, form: ProductForm):
        return bool(form.add.data)

    def parse_form(self, form: ProductForm) -> typing.List:
        purchases = []
        product_form = form.get_item_by_key(self.key)
        if self.is_added(product_form):
            person = get_primary_personal_info_from_form(form) or Person('You', '')
            for key, amount in product_form.add.data.items():
                purchases.append(Purchase(
                    person=person,
                    product_key=self.key,
                    product_option_key=key,
                    amount=amount,
                    price_each=self.base_price,
                    price=self.base_price*amount,
                    description=f'{self.name} / {self.options[key]}',
                ))
        return purchases
