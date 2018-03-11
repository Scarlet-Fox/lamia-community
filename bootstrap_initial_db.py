from woe import sqla
from woe.sqlmodels import *
from datetime import datetime
import random
import arrow

from sqlalchemy.orm.mapper import configure_mappers
configure_mappers()

sqla.create_all()