import arrow
from lamia import sqla
import lamia.sqlmodels as sqlm
from lamia import settings_file
from lamia.sqlmodels import *

sqla.engine.execute(
    """UPDATE \"user\" SET lifetime_infraction_points=0"""
)
sqla.engine.execute(
    """UPDATE \"user\" SET active_infraction_points=0"""
)

for infraction in sqlm.Infraction.query.all():
    user = infraction.recipient

    user.lifetime_infraction_points += infraction.points
    
    if arrow.now() < arrow.get(infraction.expires) and infraction.forever == False:
        user.active_infraction_points += infraction.points
        
    sqla.session.add(user)
    sqla.session.commit()
    