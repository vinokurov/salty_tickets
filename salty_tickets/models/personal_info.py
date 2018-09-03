from typing import Dict

from dataclasses import dataclass, field

@dataclass
class PersonInfo:
    full_name: str
    email: str
    location: Dict = field(default_factory=dict)
    comment: str = None
