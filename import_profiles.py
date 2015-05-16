import MySQLdb
from woe.models.core import User

db = MySQLdb.connect(user="root", db="woe")
c=db.cursor()
c.execute("select * from ipsmembers m left join ipsprofile_portal p ON m.member_id=p.pp_member_id;")

