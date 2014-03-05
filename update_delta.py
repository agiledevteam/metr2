from metrapp import app
import sqlite3

def update_delta(db):
  """update delta(sloc/floc/codefat) of all commits"""
  db.execute('update commits set delta_sloc=0, delta_floc=0, delta_codefat=0')
  cur = db.execute("""select c.id, c.sloc-p.sloc, c.floc-p.floc, c.codefat-p.codefat 
	from commits c, commits p 
	where c.parents = p.sha1 
		and c.project_id = p.project_id
		and c.sloc > 0
		and p.sloc > 0""")
  for id, sloc, floc, codefat in cur.fetchall():
    db.execute('update commits set delta_sloc=?, delta_floc=?, delta_codefat=? where id=?', [sloc,floc,codefat,id])
  db.commit()

if __name__ == '__main__':
    db = sqlite3.connect(app.config['DATABASE'])
    update_delta(db)
    db.close()

