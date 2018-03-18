from salty_tickets.database import db_session
from salty_tickets.models import Product, ProductParameter

fri_party = Product.query.filter_by(event_id=6, name='Friday Party').one()
sat_party = Product.query.filter_by(event_id=6, name='Saturday Party').one()
sun_party = Product.query.filter_by(event_id=6, name='Sunday Party').one()

musicality = Product.query.filter_by(event_id=6, name='Musicality in Shag').one()
kicks = Product.query.filter_by(event_id=6, name='Kick It').one()

fri_party.max_available = 150
fri_party.parameters.filter_by(parameter_name='party_time').one().parameter_value = '20:00-02:00'
fri_party.parameters.filter_by(parameter_name='party_location').one().parameter_value = 'Limehouse Town Hall, E147HA'
fri_party.info = 'Mind the Shag welcome party featuring great guest Hot Jazz band and DJs as well as a taster class at 8PM.'
# fri_party.parameters.append(ProductParameter(name='party_performers',value='Rokas and Ruta (St.Louis Shag taster), Jimbino Vegan & Jazz Cannibals (LIVE), Tequila Mockingbird (DJ), Patrick O\'Brien (DJ)'))

sat_party.max_available = 170
sat_party.parameters.filter_by(parameter_name='party_time').one().parameter_value = '20:00-02:00'
sat_party.parameters.filter_by(parameter_name='party_location').one().parameter_value = 'Islington Assembly Hall, N12UD'
sat_party.info = 'The Main party of the festival, featuring the London\'s superstar swing jazz bands and DJs. The party will be held in the magnificent Islington Assembly Hall, so please dress up. <br/>More tickets available at the <a href="https://app.dice.fm/event/eo87d-salty-jitterbugs-mind-the-shag-7th-apr-islington-assembly-hall-london-tickets?_branch_match_id=345519294207845104">Islington Assembly Hall page</a>'
# sat_party.parameters.append(ProductParameter(name='party_performers',value='Shirt Tail Stompers (LIVE), Michael McQuaid\'s Swing Stars (LIVE), Tequila Mockingbird (DJ)'))

sun_party.max_available = 150
sun_party.parameters.filter_by(parameter_name='party_time').one().parameter_value = '19:00-23:00'
sun_party.parameters.filter_by(parameter_name='party_location').one().parameter_value = 'JuJu\'s Bar & Stage, E16QR'
sun_party.info = 'The Mind the Shag farewell party, that is going to be more in the 50s rhythms.'
# sun_party.parameters.append(ProductParameter(name='party_performers',value='The Doel Brothers (LIVE), Lady Kamikaze (DJ)'))

musicality.max_available = 0
kicks.max_available = 0

db_session.commit()