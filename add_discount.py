from salty_tickets.config import MONGO
from salty_tickets.tasks import task_discount_created_email
from salty_tickets.tokens import GroupToken, DiscountToken
from salty_tickets.models.registrations import DiscountCode
from salty_tickets.dao import TicketsDAO

from salty_tickets import create_app
create_app()


# discount_code = DiscountCode(
#     discount_rule='free_party_pass',
#     applies_to_couple=True,
#     max_usages=1,
#     times_used=0,
#     info='Free parties discount',
#     active=True,
#     included_tickets=['party_pass'],
#     comment='Mimi & Yoshi'
# )


# discount_code = DiscountCode(
#     discount_rule='all_free',
#     applies_to_couple=True,
#     max_usages=1,
#     times_used=0,
#     info='Pay later',
#     active=True,
#     comment='Pay later'
# )



discount_code = DiscountCode(
    discount_rule='free_full_pass',
    applies_to_couple=False,
    max_usages=1,
    times_used=0,
    info='Free full pass discount',
    active=True,
    included_tickets=['full_pass'],
    comment='Lesta Woo - ticket transfer'
)

dao = TicketsDAO(host=MONGO)
event = dao.get_event_by_key('mind_the_shag_2019', get_registrations=False)
dao.add_discount_code(event, discount_code)
token = DiscountToken().serialize(discount_code)

email='alexander.a.vinokurov@gmail.com'
task_discount_created_email.send(discount_code.info, str(token), email=email)
print(token)
