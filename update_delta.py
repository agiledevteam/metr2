from metrapp import app
import sqlite3

db = sqlite3.connect(app.config['DATABASE'])

cur = db.execute('select c.id, c.sloc-p.sloc, c.floc-p.floc, c.codefat-p.codefat from commits c, commits p where c.parents = p.sha1 and c.project_id = p.project_id')
for id, sloc, floc, codefat in cur.fetchall():
    db.execute('update commits set delta_sloc=?, delta_floc=?, delta_codefat=? where id=?', [sloc,floc,codefat,id])
db.commit()

