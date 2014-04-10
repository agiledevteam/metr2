
def init(db):
	checks = [('select * from commits limit 1', 'schemas/schema.sql'),
		('select delta_sloc from commits limit 1', 'schemas/migrate.sql'),
		('select * from daily limit 1', 'schemas/migrate2.sql')]
	for sql, scriptfile in checks:
		try:
			db.execute(sql)
		except:
			run(db, scriptfile)

def run(db, scriptfile):
	print "apply " + scriptfile
	with open(scriptfile) as f:
		db.executescript(f.read())
	db.commit

if __name__ == '__main__':
	from metrapp import database
	db = database.connect_db()
	init(db)
	print "database is up to date."
