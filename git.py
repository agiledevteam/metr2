import app
from collections import namedtuple
from subprocess import call, check_output
from os import path
import re
import config
from metr import metr, stat_sum

def update(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?', [project_id])
  r = cur.fetchone()
  name, repo, branch = r[1], r[2], r[3]
  print name, repo, branch
  update_repository(name, repo, branch)
  commits = metr_repository(name, repo, branch)
  # for commit in commits:
  #   insert commit into commits (...) values (...)

def update_repository(name, repo, branch):
  repository = repo.split("//")
  repository = repository[0] + "//" + config.SSH_USERNAME + "@" + repository[1]
  if path.exists(path.join(app.GITDIR,name,".git")) :
     print "fetch..."
     call(["git","--git-dir=" + path.join(app.GITDIR,name,".git"),"--work-tree=" + path.join(app.GITDIR,name),"fetch"])
     print "merge..."
     call(["git","--git-dir=" + path.join(app.GITDIR,name,".git"),"--work-tree=" + path.join(app.GITDIR,name),"merge","origin/LG_apps_master"]) 
  else :
     print "clone..."
     call(["git","clone",repository,"-b",branch,path.join(app.GITDIR,name)])
  print "done"

def metr_repository(name, repo, branch):
  """
  Returns new commits list; follow parents until parents is already processed (stored in db)
  Alternatively, select commitid from rev-list with parents if commitid is not in database
  """
  worktree = path.join(app.GITDIR, name)
  gitdir = path.join(worktree, ".git")
  commitid = head_of(gitdir, worktree, branch) 
  [metr_commit(commitid, gitdir, worktree)]

def head_of(gitdir, worktree, branch):
  output = check_output(['git', '--git-dir=' + gitdir, '--work-tree=' + worktree, 'rev-parse', branch])
  return output.rstrip()

def parse_commit(commitid, gitdir, worktree):
  object = check_output(['git', '--git-dir=' + gitdir, '--work-tree=' + worktree, 'cat-file', 'commit', commitid])
  d = dict()
  for line in object.splitlines():
    if line == "":
      break
    values = line.split()
    d[values[0]] = "".join(values[1:])    
  return d

Commit = namedtuple('Commit', ['sha', 'meta', 'stat'])

def metr_commit(commitid, gitdir, worktree):
  """
  Returns commit(author, timestamp, ..., stat), None if 
  """
  commit = parse_commit(commitid, gitdir, worktree)
  entries = [entry for entry in ls_tree(commitid, gitdir, worktree) if not is_test(entry)]
  stats = []
  for entry in entries:
    if entry.sha in cache:
      stats.append(cache[entry.sha])
    else:
      stat = metr(read_blob(entry.sha, gitdir, worktree))
      stats.append(stat)
      cache[entry.sha] = stat
  return Commit(commitid, commit, stat_sum(stats))

def read_blob(sha, gitdir, worktree):
  src = check_output(['git', '--git-dir=' + gitdir, '--work-tree=' + worktree, 'cat-file', 'blob', sha])
  return src

test_pattern = re.compile('tests?/', re.IGNORECASE)
def is_test(entry):
  return test_pattern.search(entry.filename) != None
  
Entry = namedtuple('Entry', ['sha', 'filename'])
def ls_tree(treeish, gitdir, worktree):
  """
  Returns list of Entry(sha, name)
  """
  output = check_output(['git', '--git-dir=' + gitdir, '--work-tree=' + worktree, 'ls-tree', '-r', treeish])
  result = []
  for line in output.splitlines():
    values = line.split()
    sha, filename = values[2], values[3]
    name, ext = path.splitext(filename) 
    if ext == '.java':
      result.append(Entry(sha, filename))
  return result

# todo change this into MRU cache 
cache = dict()
  

def delete(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?',[project_id])
  r = cur.fetchone()
  print "delete ..." + path.join(app.GITDIR,r[1])
  call(["rm","-rf",path.join(app.GITDIR,r[1])])

