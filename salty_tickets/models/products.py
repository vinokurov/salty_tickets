from datetime import date, datetime

from dataclasses import dataclass, field
from salty_tickets.utils import string_to_key


@dataclass
class BaseProduct:
    name: str
    key: str = None
    info: str = None
    max_available: int = None
    base_price: float = 0
    image_url: str = None
    tags: set = field(default_factory=set)
    registrations: list = field(default_factory=list)

    def __post_init__(self):
        self.key = string_to_key(self.name)


@dataclass
class WorkshopProduct(BaseProduct):
    start_datetime: datetime = None
    end_datetime: datetime = None

    ratio: float = None
    allow_first: int = None
    level: str = None
    duration: str = None
    location: str = None
    teachers: str = None


@dataclass
class TicketProduct(BaseProduct):
    pass


@dataclass
class ProductRegistration:
    full_name: str
    email: str
    dance_role: str = None
    accepted: bool = False
