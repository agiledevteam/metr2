
# copy git commits into sqlite3
# commit message and parents -> update  commits set message=?, parents=? where...

from metrapp import app, views, database
import sqlite3
import git

gitbase = app.config['GITDIR']

def update_commit(db, id, parents, message):
    db.execute('update commits set message=?, parents=? where id=?',
                [message, parents, id])
    db.commit()

def empty_message_commits(db):
    cur = db.execute("select id, project_id, sha1 from commits where message is null or message = '' order by timestamp desc")
    return [(row[0], row[1], row[2]) for row in cur.fetchall()]

def main():
    print 'Parse commit messages.'
    db = database.get_db()
    projects = database.get_projects()
    gitmap = dict([(project["id"], git.load_git(db, project["id"])) for project in projects])
    commits = empty_message_commits(db)
    size = len(commits)
    print 'There are {0} commit(s) with empty message.'.format(size)
    count = 0
    for id, pid, sha1 in commits:
        author, timestamp, message, parents = gitmap[pid].parse_commit(sha1)
        update_commit(db, id, parents, message)
        count += 1
        if count % 100 == 0:
            print '%d/%d' % (count, size)

if __name__ == '__main__':
    with app.app_context():
        main()
