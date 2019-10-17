from salty_tickets.config import MONGO
from salty_tickets.tasks import task_group_created_email
from salty_tickets.tokens import GroupToken
from salty_tickets.models.registrations import RegistrationGroup
from salty_tickets.dao import TicketsDAO

from salty_tickets import create_app
create_app()

registration_group = RegistrationGroup(
    name='The Frenchie baguette2',
    location={'country_code': 'gb', 'city':'Norwich'},
    admin_email='alexander.a.vinokurov@gmail.com',
    comment='manually created',
)
dao = TicketsDAO(host=MONGO)
event = dao.get_event_by_key('mind_the_shag_2019', get_registrations=False)
dao.add_registration_group(event, registration_group)
token_str = GroupToken().serialize(registration_group)
task_group_created_email(registration_group.name, token_str, registration_group.admin_email)
print(token_str)