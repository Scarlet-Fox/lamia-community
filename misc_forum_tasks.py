import arrow
from woe import sqla
import woe.sqlmodels as sqlm
from woe import settings_file
from woe.sqlmodels import *

sqla.engine.execute(
    """UPDATE \"user\" SET lifetime_infraction_points=0"""
)
sqla.engine.execute(
    """UPDATE \"user\" SET active_infraction_points=0"""
)

for infraction in sqlm.Infraction.query.all():
    user = infraction.recipient

    user.lifetime_infraction_points += infraction.points
    
    if arrow.now() < arrow.get(infraction.expires) or infraction.forever == True:
        user.active_infraction_points += infraction.points
        
    sqla.session.add(user)
    sqla.session.commit()
    