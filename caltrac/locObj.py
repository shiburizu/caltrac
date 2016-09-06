import sqlite3 as sql
#localization database -- should exist at runtime.
ldb = sql.connect('caltrac/li0n.db',detect_types=sql.PARSE_DECLTYPES)
lc = ldb.cursor()

#todo move getdict here
