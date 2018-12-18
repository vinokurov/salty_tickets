from salty_tickets.config import MONGO
from salty_tickets.tokens import GroupToken, DiscountToken
from salty_tickets.models.registrations import DiscountCode
from salty_tickets.dao import TicketsDAO

discount_code = DiscountCode(
    discount_rule='free_party_pass',
    applies_to_couple=False,
    max_usages=1,
    times_used=0,
    info='Free parties discount',
    active=True,
    included_tickets=['party_pass']
)

# discount_code = DiscountCode(
#     discount_rule='free_full_pass',
#     applies_to_couple=False,
#     max_usages=1,
#     times_used=0,
#     info='Free full pass discount',
#     active=True,
#     included_tickets=['full_pass']
# )

dao = TicketsDAO(host=MONGO)
event = dao.get_event_by_key('mind_the_shag_2019')
dao.add_discount_code(event, discount_code)
token = DiscountToken().serialize(discount_code)
print(token)
