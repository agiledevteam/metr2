
# copy git commits into sqlite3
# commit message and parents -> update  commits set message=?, parents=? where... 

from metrapp import app, views
import sqlite3
import git

gitbase = app.config['GITDIR']

def update_commit(db, id, project, g, sha1):
    author,timestamp,message,parents = g.parse_commit(sha1)
    db.execute('update commits set message=?, parents=? where id=?',
                [message, parents, id])
    db.commit()

def empty_message_commits(db):
    cur = db.execute('select id, project_id, sha1 from commits where message is null')
    return [(row[0], row[1], row[2]) for row in cur.fetchall()]

with app.app_context():
    db = views.get_db()
    projects = views.Project.all()
    projmap = dict([(project.id, project) for project in projects])
    gitmap = dict([(project.id, git.load_git(db, project.id)) for project in projects])
    commits = empty_message_commits(db)
    size = len(commits)
    count = 0
    for id, pid, sha1 in commits:
        update_commit(db, id, projmap[pid], gitmap[pid], sha1)
        count += 1 
        if count % 100 == 0: 
            print '%d/%d' % (count, size)
