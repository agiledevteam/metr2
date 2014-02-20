import app
from collections import namedtuple
from subprocess import call, check_output
from os import path
import random
import re
import config
from metr import metr, stat_sum, Stat

Commit = namedtuple('Commit', ['sha1', 'author', 'timestamp', 'parents', 'sloc', 'dloc', 'cc'])

Entry = namedtuple('Entry', ['sha1', 'filename'])

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

  def rev_list(self, branch):
    output = check_output(self.base_cmd + ['rev-list', branch])
    commits = output.splitlines()
    return commits
    #random.shuffle(commits)
    #return commits[0:10]

  def parse_commit(self, commitid):
    "Parse commit object info and return (author,timestamp,parents)"
    obj = check_output(self.base_cmd + ['log', '-1', '--pretty=raw', commitid])
    author = 'unknown'
    timestamp = 0
    parents = []
    for line in obj.splitlines():
      if line == "":
        break
      values = line.split()
      if values[0] == 'author':
        author, timestamp = values[-3].strip('<>').lower(), int(values[-2])
      elif values[0] == 'parent':
        parents += [values[1]]
    return author, timestamp, parents

  def ls_tree(self, treeish):
    """ Returns list of Entry(sha1, name) """
    output = check_output(self.base_cmd + ['ls-tree', '-r', treeish])
    result = []
    for line in output.splitlines():
      values = line.split()
      sha1, filename = values[2], values[3]
      name, ext = path.splitext(filename) 
      if ext == '.java':
        result.append(Entry(sha1, filename))
    return result

  def parse_blob(self, sha1):
    src = check_output(self.base_cmd + ['cat-file', 'blob', sha1])
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

  def already_processed(commitid):
    cur = db.execute('select count(*) from commits where sha1 = ?', [commitid])
    row = cur.fetchone()
    return row[0] > 0

  def after_processing(commit):
    db.execute('insert into commits (project_id, author, timestamp, sha1, sloc, dloc, cc) values (?,?,?,?,?,?,?)', [project_id, commit.author, commit.timestamp, commit.sha1, commit.sloc, commit.dloc, commit.cc])
    db.commit()

  metr_repository(git, already_processed, after_processing)

def metr_repository(git, already_processed, after_processing):
  print len(cache)
  count = 0
  ids = git.rev_list('HEAD')
  while len(ids) > 0:
    commitid = ids.pop(0)
    if already_processed(commitid):
      continue
    commit = metr_commit(commitid, git)
    after_processing(commit)
    count += 1
#    if count > 1:
#      print "break after processing", count, "commits"
#      break

def metr_commit(commitid, git):
  """
  Returns commit , recover parse/metr failure
  """
  author, timestamp, parents = git.parse_commit(commitid)
  print commitid[:7],
  entries = [entry for entry in git.ls_tree(commitid) if not is_test(entry)]
  print len(entries),'file(s) ...',
  stat = Stat(sloc=0, dloc=0, cc=1)

  stats = []
  for entry in entries:
    if entry.sha1 in cache:
      stats.append(cache[entry.sha1])
    else:
      try:
        blob = git.parse_blob(entry.sha1)
        stat_ = metr(blob)
        cache[entry.sha1] = stat_
        stats.append(stat_)
      except:
        print "failed with", entry
        break
  else:
    print "done"
    stat = stat_sum(stats)
  return Commit(commitid, author, timestamp, parents, stat.sloc, stat.dloc, stat.cc)

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

