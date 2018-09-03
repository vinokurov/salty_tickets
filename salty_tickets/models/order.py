from datetime import datetime
from typing import List, Dict

from dataclasses import dataclass, field
from salty_tickets.constants import NEW, SUCCESSFUL


@dataclass
class Payment:
    price: float
    transaction_fee: float = 0

    status: str = NEW
    stripe_details: dict = field(default_factory=dict)
    date: datetime = field(default_factory=datetime.utcnow)


