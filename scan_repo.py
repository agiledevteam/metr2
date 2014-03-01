import os
from subprocess import check_output
from os.path import join, relpath
import sqlite3
from metrapp import app, views

def find_gits(repo):
  for root, dirs, files in os.walk(repo):
    if '.git' in dirs:
      dirs[:] = []
      yield relpath(root, repo) 

def get_all_projects(db):
  cur = db.execute('select name from projects')
  return [row[0] for row in cur.fetchall()]

def add_to_metr(db, gitbase, name):
  worktree = os.path.join(gitbase, name)
  gitdir = os.path.join(worktree, '.git')
  repository = check_output(['git', '--git-dir=' + gitdir,
    'ls-remote', '--get-url']).rstrip()
  branch = check_output(['git', '--git-dir=' + gitdir,
    'rev-parse', '--abbrev-ref', 'HEAD']).rstrip()
  db.execute('insert into projects (name, repository, branch) values (?,?,?)', 
       [name, repository, branch])

def main():
  db = sqlite3.connect(app.config['DATABASE'])
  all_projects = get_all_projects(db)
  gitbase = app.config['GITDIR']
  added = 0
  for name in find_gits(gitbase):
    if not name in all_projects:
      add_to_metr(db, gitbase, name)
      print 'found', name, 'and added it to metr.'
      added += 1
    else:
      print 'found', name, 'but metr already has it.' 
  db.commit()    
  if added > 0:
    print added, 'project(s) added, need to run "python update_all.py"
  db.close()

if __name__ == '__main__':
  main()
