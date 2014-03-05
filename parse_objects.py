
# temporarily 
# run this script to cancel out all commits which include a file with compilation errors.
# after run this script, run 'update_delta.py' also to update delta information in the database.

from metrapp import app, views
import git
import metr
from pygit2 import Repository
import metr
import os
from redis import Redis
import pickle
from collections import namedtuple

gitbase = app.config['GITDIR']
redis = Redis()

Project = namedtuple('Project', ['id', 'name'])

def main():
    for project in get_all_projects():
        parse_all_objects(project)

def get_all_projects():
    return [Project(project['id'], project['name']) for project in views.get_projects()]

def parse_all_objects(project):
    g = git.load_git(views.get_db(), project.id)
    r = Repository(os.path.join(gitbase, project.name, '.git'))
    errors = get_error_files(g, r, project)
    mark_error_commits(g, project, errors)

def get_error_files(g, r, project):
    errors = set()
    all_file_ids = get_all_file_ids(g)
    size = len(all_file_ids)
    for i, blob_id in enumerate(all_file_ids):
        print i, size, project.name, 'blob', blob_id
        stat = metr_blob(project, blob_id, r)
        if stat == (-1, -1):
            errors.add(blob_id)
    return errors

def metr_blob(project, blob_id, r):
    redis_key = "blob:%s" % (project.id,)    
    stat = redis.hget(redis_key, blob_id)
    if stat != None:
      return pickle.loads(stat)
    else:
      stat = metr_blob_(r[blob_id].data) 
      redis.hset(redis_key, blob_id, pickle.dumps(stat))
      return stat

def metr_blob_(blob_data):
    try:
        return tuple(metr.metr(normalize_newline(blob_data)))
    except KeyboardInterrupt:
        raise
    except:
        return (-1, -1)

def normalize_newline(data):
    return data.replace('\r\n', '\n').replace('\r', '\n')

def get_all_file_ids(g):
    file_ids = []
    for line in g.cmd('rev-list', '--objects', 'HEAD'):
        values = line.split()
        if len(values) == 1:
            continue
        if git.is_java(values[1]):
            file_ids.append(values[0])
    return file_ids

def mark_error_commits(g, project, errors):
    print project.name, errors
    if len(errors) == 0:
        return 0 

    all_commits = rev_list(g)
    size = len(all_commits)
    error_commits = []
    for i, commit_id in enumerate(all_commits):
        print  i, size, project.name, 'commit', commit_id
        if not set(ls_tree(g, commit_id)).isdisjoint(errors):
            error_commits.append((project.id, commit_id))

    db = views.get_db()
    db.executemany('update commits set sloc=-1, floc=-1, codefat=0 where project_id=? and sha1=?', error_commits)
    db.commit()
    return len(error_commits) 

def rev_list(g):
    return g.rev_list('HEAD')

def ls_tree(g, commit_id):
    return map(lambda entry: entry.sha1, g.ls_tree(commit_id))

if __name__ == '__main__':
    with app.app_context():
        main()

