import app
from collections import namedtuple
from subprocess import call, check_output
from os import path
import re
import config
from metr import metr, stat_sum

Commit = namedtuple('Commit', ['sha', 'meta', 'stat'])

Entry = namedtuple('Entry', ['sha', 'filename'])

class Git(object):
  def __init__(self, repository, gitdir, worktree, branch):
    self.repository = repository
    self.gitdir = gitdir
    self.worktree = worktree
    self.branch = branch
    self.base_cmd = ["git","--git-dir=" + gitdir,"--work-tree=" + worktree]

  def update(self):
    if self.cloned():
      self.fetch()
      self.merge()
    else:
      self.clone()

  def cloned(self):
    return path.exists(self.gitdir)

  def fetch(self):
    call(self.base_cmd + ['fetch'])
  
  def merge(self):
    call(self.base_cmd + ['merge', 'origin/' + self.branch])
  
  def clone(self):
    call(['git', 'clone', self.repository, '-b', self.branch, self.worktree])

  def rev_parse(self, branch):
    output = check_output(self.base_cmd + ['rev-parse', branch])
    return output.rstrip()

  def parse_commit(self, commitid):
    object = check_output(self.base_cmd + ['cat-file', 'commit', commitid])
    d = dict()
    for line in object.splitlines():
      if line == "":
        break
      values = line.split()
      d[values[0]] = "".join(values[1:])    
    return d

  def ls_tree(self, treeish):
    """
    Returns list of Entry(sha, name)
    """
    output = check_output(self.base_cmd + ['ls-tree', '-r', treeish])
    result = []
    for line in output.splitlines():
      values = line.split()
      sha, filename = values[2], values[3]
      name, ext = path.splitext(filename) 
      if ext == '.java':
        result.append(Entry(sha, filename))
    return result

  def parse_blob(self, sha):
    src = check_output(self.base_cmd + ['cat-file', 'blob', sha])
    return src


def update(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?', [project_id])
  r = cur.fetchone()
  name, repo, branch = r[1], r[2], r[3]
  print name, repo, branch

  # insert ssh_username 
  if config.SSH_USERNAME != None and config.SSH_USERNAME != "":
    parts = repo.split("//")
    repo = parts[0] + "//" + config.SSH_USERNAME + "@" + parts[1]

  gitdir = path.join(app.GITDIR, name, '.git')
  worktree = path.join(app.GITDIR, name)
  git = Git(repo, gitdir, worktree, branch)

  git.update()
  commits = metr_repository(git)
  # for commit in commits:
  #   insert commit into commits (...) values (...)

def metr_repository(git):
  """
  Returns new commits list; follow parents until parents is already processed (stored in db)
  Alternatively, select commitid from rev-list with parents if commitid is not in database
  """
  commitid = git.rev_parse('HEAD')
  [metr_commit(commitid, git)]

def metr_commit(commitid, git):
  """
  Returns commit(author, timestamp, ..., stat), None if 
  """
  commit = git.parse_commit(commitid)
  entries = [entry for entry in git.ls_tree(commitid) if not is_test(entry)]
  stats = []
  for entry in entries:
    if entry.sha in cache:
      stats.append(cache[entry.sha])
    else:
      stat = metr(git.parse_blob(entry.sha))
      stats.append(stat)
      cache[entry.sha] = stat
  return Commit(commitid, commit, stat_sum(stats))

test_pattern = re.compile('tests?/', re.IGNORECASE)
def is_test(entry):
  return test_pattern.search(entry.filename) != None
  
# todo change this into MRU cache 
cache = dict()
  

def delete(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?',[project_id])
  r = cur.fetchone()
  print "delete ..." + path.join(app.GITDIR,r[1])
  call(["rm","-rf",path.join(app.GITDIR,r[1])])

