import sqlite3 as sql
db = sql.connect('caltrac/user.db',detect_types=sql.PARSE_DECLTYPES)
c = db.cursor()

class dbHandler(object):
	def buildTables(self):
		c.execute('''CREATE TABLE IF NOT EXISTS user(func TEXT UNIQUE, name TEXT,
		 height REAL, weight REAL, age INTEGER, gender TEXT	, rating INTEGER, pregnancy INTEGER);''')
		c.execute('''CREATE TABLE IF NOT EXISTS foods(name TEXT, date DATE, kcal REAL, 
		portion REAL);''')
		c.execute('''CREATE TABLE IF NOT EXISTS calendar(date TEXT UNIQUE, total REAL,
		 avg REAL, len INTEGER);''')
		
#must exist at runtime
ldb = sql.connect('caltrac/caltrac.db',detect_types=sql.PARSE_DECLTYPES)
lc = ldb.cursor()

#todo move getdict here
