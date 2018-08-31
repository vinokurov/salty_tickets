from dataclasses import dataclass, field

@dataclass
class PersonalInfo:
    full_name: str
    email: str
    location: dict = field(default_factory=dict)
    dance_role: str = None
    comment: str = None