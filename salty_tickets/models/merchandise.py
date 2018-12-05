import typing

from salty_tickets.utils.utils import string_to_key
from wtforms import Form as NoCsrfForm
from dataclasses import dataclass, field
from salty_tickets.forms import RawField


class MerchandiseProductForm(NoCsrfForm):
    add = RawField()


@dataclass
class MerchandiseProduct:
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
        return MerchandiseProductForm
