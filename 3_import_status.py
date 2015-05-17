import MySQLdb
import MySQLdb.cursors
from woe.models.core import User, StatusUpdate, StatusComment

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsmember_status_updates;")

