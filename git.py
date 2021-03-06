from metrapp import app, database
from collections import namedtuple
from subprocess import call, STDOUT
import subprocess
from os import path
import random
import re
import config
from metr import metr, stat_sum, Stat
from pygit2 import Repository
from redis import Redis
import pickle

redis = Redis()

test_pattern = re.compile('tests?/', re.IGNORECASE)

Commit = namedtuple('Commit', ['sha1', 'author', 'timestamp', 'message', 'parents', 'sloc', 'floc', 'codefat'])

Entry = namedtuple('Entry', ['sha1', 'filename'])

Diff = namedtuple('Diff', ['new', 'old', 'status'])

def check_output(*args, **kwargs):
  try:
    return subprocess.check_output(*args, **kwargs)
  except:
    print "error", args, kwargs
    return ""

class GitCmd(object):
  def __init__(self, gitdir, worktree):
    self.gitdir = gitdir
    self.worktree = worktree
    self.base_cmd = ["git","--git-dir=" + gitdir,"--work-tree=" + worktree]
  def cmd(self, *args):
    output = check_output(self.base_cmd + list(args))
    return output.splitlines()

class Git(object):
  def __init__(self, repository, gitdir, worktree, branch):
    self.repository = repository
    self.gitdir = gitdir
    self.worktree = worktree
    self.branch = branch
    self.base_cmd = ["git","--git-dir=" + gitdir,"--work-tree=" + worktree]

  def update(self):
    if self.cloned():
      if self.fetch():
        self.resetToOriginMaster()
        return True
      return False
    else:
      self.clone()
      return True

  def cloned(self):
    return path.exists(self.gitdir)

  def cmd(self, *args):
    output = check_output(self.base_cmd + list(args))
    return output.splitlines()

  def fetch(self):
    "return true if some are fetched"
    output = check_output(self.base_cmd + ['fetch', '-n'], stderr=STDOUT)
    return output != ""

  def resetToOriginMaster(self):
    call(self.base_cmd + ['reset', '--hard', 'origin/' + self.branch])

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
    "Parse commit object info and return (author,timestamp,message,parents)"
    obj = check_output(self.base_cmd + ['log', '-1', '--pretty=raw', commitid])
    return parse_commit_(obj)

  def ls_tree(self, treeish):
    """ Returns list of Entry(sha1, name) """
    output = check_output(self.base_cmd + ['ls-tree', '-r', treeish])
    result = []
    for line in output.splitlines():
      values = line.split()
      sha1, filename = values[2], values[3]
      if is_java(filename):
        result.append(Entry(sha1, filename))
    return result

  def get_hash_by_path(self, tree, path):
    # '100644 blob cf484376827c5299a7ef9e0336a783adc0dc1ee4\tmetrapp/apis.py\n'
    src = check_output(self.base_cmd + ['ls-tree', tree, '--', path])
    return src.split()[2]

  def parse_blob(self, sha1 = None, path = None, tree = None):
    if path != None:
      if tree == None:
        tree = 'origin/' + self.branch
      sha1 = self.get_hash_by_path(tree, path)
    src = check_output(self.base_cmd + ['cat-file', 'blob', sha1], universal_newlines=True)
    return src

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
      if is_java(newfilename):
        diff.append(Diff(status=status[0], new=dict(filename=newfilename, sha1=newsha1), old=dict(filename=oldfilename, sha1=oldsha1)))
    return diff

def load_git(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?', [project_id])
  r = cur.fetchone()
  name, repo, branch = r[1], r[2], r[3]

  # insert ssh_username
  if config.SSH_USERNAME != None and config.SSH_USERNAME != "":
    parts = repo.split("//")
    if len(parts) >= 2:
      repo = parts[0] + "//" + config.SSH_USERNAME + "@" + parts[1]

  gitdir = get_gitdir(name)
  worktree = get_worktree(name)
  return Git(repo, gitdir, worktree, branch)

def update(db, project_id):
  git = load_git(db, project_id)
  if git.update():
    metr_repository(git, db, project_id)

def metr_repository(git, db, project_id):
  cur = db.execute('select sha1 from commits where project_id = ?', (project_id,))
  commits_in_db = set(row[0] for row in cur.fetchall())
  commits_in_git = git.rev_list('--remotes') # get all commits from all branches

  for commit_id in commits_in_git:
    if not commit_id in commits_in_db:
      commit = metr_commit(git, project_id, commit_id)
      insert_commit(db, project_id, commit)

def metr_commit(git, project_id, commit_id):
  """
  Returns commit , recover parse/metr failure
  """
  author, timestamp, message, parents = git.parse_commit(commit_id)
  print commit_id[:7],
  entries = git.ls_tree(commit_id)
  print len(entries),'file(s) ...',
  stat = Stat(sloc=0, floc=0)

  stats = []
  for entry in entries:
    try:
      stat0 = metr_blob(git, project_id, entry.sha1)
      stats.append(stat0)
    except KeyboardInterrupt:
      raise
    except:
      print "failed with", entry
      break
  else:
    print "done"
    stat = stat_sum(stats)
  return Commit(commit_id, author, timestamp, message, parents, stat.sloc, stat.floc, codefat(stat))

def metr_blob(git, project_id, sha1):
  "May raise exception"
  assert len(sha1) == 40
  key = 'codefat:' + str(project_id)
  stat = redis.hget(key, sha1)
  if stat is None:
    blob = git.parse_blob(sha1)
    stat = metr(blob)
    redis.hset(key, sha1, pickle.dumps(stat))
    return stat
  else:
    return pickle.loads(stat)

def delete(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?',[project_id])
  r = cur.fetchone()
  print "delete ..." + path.join(app.config['GITDIR'],r[1])
  call(["rm","-rf",path.join(app.config['GITDIR'],r[1])])

def ls_tree(db, project_id, sha1):
  "Returns file list of sha1 commit in project_id project"
  git = load_git(db, project_id)
  files = git.ls_tree(sha1)
  return [dict(f._asdict()) for f in files]

def metr_file(git, project_id, file):
  try:
    stat = metr_blob(git, project_id, file['sha1'])
  except KeyboardInterrupt:
    raise
  except:
    stat = Stat(sloc=0, floc=0)
    file['status'] = 'error'
  file['sloc'] = stat.sloc
  file['floc'] = stat.floc
  file['codefat'] = codefat(stat)

def diff_tree(db, project_id, sha1):
  git = load_git(db, project_id)
  diffs = git.diff_tree(sha1)
  return [each._asdict() for each in diffs]

def resolve(db, project_id, ref):
  git = load_git(db, project_id)
  return git.rev_parse(ref)

def hunk_for_old(hunk):
  lines = []
  line_no = hunk.old_start
  for kind, line in hunk.lines:
    if kind == ' ':
      lines.append((line_no, '', line))
    elif kind == '-':
      lines.append((line_no, 'deleted', line))
    else:
      lines.append((line_no, 'empty', ' '))
    line_no += 1
  return lines

def hunk_for_new(hunk):
  lines = []
  line_no = hunk.new_start
  for kind, line in hunk.lines:
    if kind == ' ':
      lines.append((line_no, '', line))
    elif kind == '-':
      lines.append((line_no, 'empty', ' '))
    else:
      lines.append((line_no, 'added', line))
    line_no += 1
  return lines

def hunk_lines(hunk):
  lines = []
  line_no = hunk.old_start
  for kind, line in hunk.lines:
    if kind == ' ':
      lines.append((line_no, '', line))
    elif kind == '-':
      lines.append((line_no, 'deleted', line))
    else:
      lines.append((line_no, 'added', line))
    line_no += 1
  return lines

# def diff(db, project_id, old, new):
#   repo = get_repository(db, project_id)
#   old_blob = repo[old]
#   new_blob = repo[new]
#   patch = old_blob.diff(new_blob)
#   old_lines = [(line_no + 1, '', line_text) for line_no, line_text in enumerate(old_blob.data.splitlines())]
#   new_lines = [(line_no + 1, '', line_text) for line_no, line_text in enumerate(new_blob.data.splitlines())]
#   for hunk in reversed(patch.hunks):
#     old_lines[hunk.old_start-1:hunk.old_start + hunk.old_lines - 1] = hunk_for_old(hunk)
#     new_lines[hunk.new_start-1:hunk.new_start + hunk.new_lines - 1] = hunk_for_new(hunk)
#   old_lines = [dict(no=line[0], kind=line[1], text=line[2]) for line in old_lines]
#   new_lines = [dict(no=line[0], kind=line[1], text=line[2]) for line in new_lines]
#   return old_lines, new_lines


def iterate_hunks(lines):
  hunk = []
  for line in lines:
    if line[0:4] == 'diff': # diff
      if len(hunk) != 0:
        yield hunk
        hunk = []
    hunk.append(line)
  if len(hunk) != 0:
    yield hunk

def format_hunk(hunk):
  lines = []
  for line in hunk:
    if line[0] == '+':
      lines.append(('added', line))
    elif line[0] == '-':
      lines.append(('deleted', line))
    elif line[0] == '@':
      lines.append(('context', line))
    else:
      lines.append(('', line))
  return [dict(kind=kind, text=line) for kind, line in lines]

def hunk_index(hunk):
  for line in hunk:
    if line[0] == 'i':
      return line.split()[1].split("..")
  raise KeyError()

def parse_diff_patch(patch, old, new):
  lines = filter(lambda line: len(line) != 0, patch.splitlines())
  for hunk in iterate_hunks(lines):
    a, b = hunk_index(hunk)
    if old.startswith(a) and new.startswith(b):
      return format_hunk(hunk)
  return None

def diff(db, project_id, sha1, old, new):
  repo = get_repository(db, project_id)
  commit = repo.get(sha1)
  for parent in commit.parents:
    diff = repo.diff(parent, commit)
    file_diffs = parse_diff_patch(diff.patch, old, new)
    if file_diffs != None:
      return file_diffs
  raise KeyError()

def get_gitdir(project_name):
  return path.join(app.config['GITDIR'], project_name, '.git')

def get_worktree(project_name):
  return path.join(app.config['GITDIR'], project_name)

def get_repository(db, project_id):
  cur = db.execute('select name from projects where id=?', (project_id,))
  project_name, = cur.fetchone()
  return Repository(get_gitdir(project_name))

def codefat(stat):
  if stat.sloc == 0:
    return 0
  else:
    return 100 * stat.floc/stat.sloc

def rev_list(project_name, branch):
  cmd = GitCmd(get_gitdir(project_name), get_worktree(project_name))
  return cmd.cmd("rev-list", branch)

def rev_list_first_parent(db, project_id):
  git = load_git(db, project_id)
  return git.cmd('rev-list', '--first-parent', 'HEAD')

def decode(s):
  try:
    return s.decode('utf-8')
  except:
    try:
      return s.decode('euc-kr')
    except:
      return s.decode('utf-8', errors='ignore')

def is_java(filename):
  name, ext = path.splitext(filename)
  return test_pattern.search(filename) == None and ext == ".java"

def insert_commit(db, project_id, commit):
  db.execute('insert into commits (project_id, author, timestamp, message, parents, sha1, sloc, floc, codefat) values (?,?,?,?,?,?,?,?,?)',
        [project_id, commit.author, commit.timestamp, commit.message, commit.parents, commit.sha1, commit.sloc, commit.floc, commit.codefat])
  db.commit()

def parse_branchline(line):
  origin_prefix = "origin/"
  branch = line.strip()
  if branch.startswith(origin_prefix) and branch.find("->") == -1:
    return dict(name=branch[len(origin_prefix):])
  return None

def get_branches(project_name):
  branches = []
  cmd = GitCmd(get_gitdir(project_name), get_worktree(project_name))
  for line in cmd.cmd("branch", "-r"):
    branch = parse_branchline(line)
    if branch:
      branches.append(branch)
  return branches

def parse_commit_(obj):
  lines = obj.splitlines()

  try:
    index = lines.index('')
    message = '\n'.join(lines[index+1:])
    lines = lines[:index]
  except ValueError:
    message = ''

  author = 'unknown'
  timestamp = 0
  parents = []
  for line in lines:
    values = line.split()
    if len(values) == 0: # such as mergetag object can contain " " line
      continue
    if values[0] == 'author':
      author, timestamp = values[-3].strip('<>').lower(), int(values[-2])
    elif values[0] == 'parent':
      parents += [values[1]]
  return decode(author), timestamp, decode(message), " ".join(parents)

def get_stats(git, project_id, arr):
  "return [Stat(sloc,floc)] for each sha1 in arr"
  return [metr_blob(git, project_id, sha1) for sha1 in arr]
