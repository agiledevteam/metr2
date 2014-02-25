from metrapp import app
from collections import namedtuple
from subprocess import call, check_output
from os import path
import random
import re
import config
from metr import metr, stat_sum, Stat

test_pattern = re.compile('tests?/', re.IGNORECASE)

Commit = namedtuple('Commit', ['sha1', 'author', 'timestamp', 'parents', 'sloc', 'dloc', 'cc'])

Entry = namedtuple('Entry', ['sha1', 'filename'])

Diff = namedtuple('Diff', ['new', 'old', 'status'])

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
      if self.filter(filename):
        result.append(Entry(sha1, filename))
    return result
  
  def parse_blob(self, sha1):
    src = check_output(self.base_cmd + ['cat-file', 'blob', sha1], universal_newlines=True)
    return src

  def filter(self,filename):
    name, ext = path.splitext(filename) 
    return test_pattern.search(filename) == None and ext == ".java"
   
  def diff_tree(self, sha1):
    output = check_output(self.base_cmd + ['diff-tree', '-r', '--root', '-m', '--no-renames', '--no-commit-id', sha1])
    diff = [] 
    for line in output.splitlines():
      values = line.split()
      oldsha1, newsha1, status, oldfilename = values[2], values[3], values[4], values[5] 
      if len(values) == 7:
        newfilename = values[6]
      else:
        newfilename = oldfilename 
      if self.filter(newfilename): 
        diff.append(Diff(status=status[0], new=dict(filename=newfilename, sha1=newsha1), old=dict(filename=oldfilename, sha1=oldsha1)))
    return diff

def load_git(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?', [project_id])
  r = cur.fetchone()
  name, repo, branch = r[1], r[2], r[3]

  # insert ssh_username 
  if config.SSH_USERNAME != None and config.SSH_USERNAME != "":
    parts = repo.split("//")
    repo = parts[0] + "//" + config.SSH_USERNAME + "@" + parts[1]

  gitdir = path.join(app.GITDIR, name, '.git')
  worktree = path.join(app.GITDIR, name)
  return Git(repo, gitdir, worktree, branch)

def update(db, project_id):
  git = load_git(db, project_id)
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
    if count > 10:
      print "break after processing", count, "commits"
      break

def metr_commit(commitid, git):
  """
  Returns commit , recover parse/metr failure
  """
  author, timestamp, parents = git.parse_commit(commitid)
  print commitid[:7],
  entries = git.ls_tree(commitid)
  print len(entries),'file(s) ...',
  stat = Stat(sloc=0, dloc=0, cc=1)

  stats = []
  for entry in entries:
    try:
      stats.append(metr_blob(git, entry.sha1))
    except:
      print "failed with", entry
      break
  else:
    print "done"
    stat = stat_sum(stats)
  return Commit(commitid, author, timestamp, parents, stat.sloc, stat.dloc, stat.cc)

def metr_blob(git, sha1):
  "May raise exception"
  if sha1 in cache:
    return cache[sha1]
  try: 
    blob = git.parse_blob(sha1)
    stat_ = metr(blob)
    cache[sha1] = stat_
    return stat_
  except:
    return Stat(sloc=0,dloc=0,cc=1)

# todo change this into MRU cache 
cache = dict()
  

def delete(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?',[project_id])
  r = cur.fetchone()
  print "delete ..." + path.join(app.GITDIR,r[1])
  call(["rm","-rf",path.join(app.GITDIR,r[1])])

def ls_tree(db, project_id, sha1):
  "Returns file list of sha1 commit in project_id project"
  git = load_git(db, project_id)
  files = git.ls_tree(sha1)
  return [dict(f._asdict()) for f in files]

def diff_tree(db, project_id, sha1):
  git = load_git(db, project_id)
  def metr_file(file):
    stat = metr_blob(git, file['sha1'])
    file['sloc'] = stat.sloc
    file['dloc'] = stat.dloc
    file['codefat'] = codefat(stat)
    return file
  diffs = git.diff_tree(sha1)
  return [dict(status=diff.status, old=metr_file(diff.old), new=metr_file(diff.new)) for diff in diffs]

def codefat(stat):
  if stat.sloc == 0:
    return 0
  else:
    return 100 * (1-stat.dloc/stat.sloc)

def get_commit(db, project_id, sha1):
  if sha1 == 'HEAD':
    cur = db.execute('select id,project_id,author,timestamp,sha1,sloc,dloc,100*(1-dloc/sloc) from commits where project_id=? order by timestamp desc limit 1', [project_id])
  else:
    cur = db.execute('select id,project_id,author,timestamp,sha1,sloc,dloc,100*(1-dloc/sloc) from commits where sha1 like ?', [sha1 + '%'])
  row = cur.fetchone()
  commit = dict(id=row[0],project_id=row[1],author=row[2],timestamp=row[3],sha1=row[4],sloc=row[5],dloc=row[6],codefat=row[7])
  return commit

