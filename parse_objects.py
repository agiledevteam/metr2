
# temporarily 
# run this script to cancel out all commits which include a file with compilation errors.
# after run this script, run 'update_delta.py' also to update delta information in the database.

from metrapp import app, views
import git
import metr
from pygit2 import Repository
import metr
import os

gitbase = app.config['GITDIR']

def main():
    for project in get_all_projects():
        parse_all_objects(project['id'], project['name'])

def get_all_projects():
    return views.get_projects()

def parse_all_objects(project_id, project_name):
    g = git.load_git(views.get_db(), project_id)
    r = Repository(os.path.join(gitbase, project_name, '.git'))
    errors = get_error_files(g, r, project_name)
    mark_error_commits(g, project_id, project_name, errors)

def get_error_files(g, r, project_name):
    errors = set()
    all_file_ids = get_all_file_ids(g)
    size = len(all_file_ids)
    for i, blob_id in enumerate(all_file_ids):
        print i, size, project_name, 'blob', blob_id
        if not metr_succeeded(g, r, blob_id):
            errors.add(blob_id)
    return errors

def metr_succeeded(g, r, blob_id):
    try:
        data = r[blob_id].data
        metr.metr(normalize_newline(data))
        return True
    except KeyboardInterrupt:
        raise
    except:
        return False

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

def mark_error_commits(g, project_id, project_name, errors):
    count = 0

    print project_name, errors
    if len(errors) == 0:
        return count

    all_commits = rev_list(g)
    size = len(all_commits)
    for i, commit_id in enumerate(all_commits):
        print  i, size, project_name, 'commit', commit_id
        if not set(ls_tree(g, commit_id)).isdisjoint(errors):
            db = views.get_db()
            db.execute('update commits set sloc=0, floc=0, codefat=0 where project_id=? and sha1=?', (project_id, commit_id))
            db.commit()
            count += 1
    return count

def rev_list(g):
    return g.rev_list('HEAD')

def ls_tree(g, commit_id):
    return map(lambda entry: entry.sha1, g.ls_tree(commit_id))

if __name__ == '__main__':
    with app.app_context():
        main()

