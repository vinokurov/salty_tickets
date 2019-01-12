from datetime import datetime

from salty_tickets.config import MONGO
from salty_tickets.dao import TicketsDAO, TicketDocument
from salty_tickets.models.tickets import WorkshopTicket

TIME_SUN_2 = {'start_datetime': datetime(2019, 3, 31, 14, 0),
              'end_datetime': datetime(2019, 3, 31, 16, 0)}

TIME_SUN_3 = {'start_datetime': datetime(2019, 3, 31, 16, 30),
              'end_datetime': datetime(2019, 3, 31, 18, 30)}

TEACH_FC = 'Cherry & Filip'
TEACH_HL = 'Larissa & Heiko'

LEV_CSH = 'Collegiate Shag'
LEV_VET = 'Collegiate Shag Veteran'

dao = TicketsDAO(host=MONGO)

event_doc = dao._get_event_doc('mind_the_shag_2019')

event_doc.pricing_rules[0]['kwargs']['price_cheaper_station_extra'] = 15.0
event_doc.layout['workshops']['Sunday'][1]['3'] = 'shag_dynamite'
event_doc.layout['workshops']['Sunday'][2]['3'] = 'solo_shag'

kwargs_station = dict(
    ratio=1.5,
    allow_first=5,
    max_available=30,
    base_price=35.0,
    tags={'station', 'cheaper_station'}
)

tickets = [
    WorkshopTicket(
        name='Shag Dynamite',
        info="Looking for more power moves for competitions, performances or to spice up your social Shag? In this station Larissa & Heiko, the Jitterbugs from Basel, who have competed in almost every major Shag event in the world, are going to share their favourite killer moves!",
        teachers=TEACH_HL,
        level=LEV_VET,
        **kwargs_station,
        **TIME_SUN_2,
    ),
    WorkshopTicket(
        name='Solo Shag',
        info="Join the latest trend in the Shag community all over the world! As well as being great fun to dance alone, Solo Shag will also enhance your partner dancing by building your confidence in developing your own personal variations; great for leaders and followers alike! In this station with Cherry and Filip, the pioneers of the style, you will work both solo and in couples. You will learn a 1-minute choreography that will be performed later at the party.",
        teachers=TEACH_FC,
        level=LEV_CSH,
        **kwargs_station,
        **TIME_SUN_3,
    ),
]

event_doc.tickets.update({t.key: TicketDocument.from_dataclass(t) for t in tickets})

event_doc.save()
