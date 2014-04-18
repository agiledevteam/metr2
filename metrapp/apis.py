from flask import jsonify, json, request
from datetime import datetime, date, timedelta
import time
# metr
from metrapp import app
from metrapp.views import get_db
import git
from database import *
from collections import OrderedDict
from itertools import izip
from rediscache import rediscache
from collections import namedtuple

@app.route('/api/projects2')
def api_projects2():
  return api_projects2_()

def remove_duplicates(arr, key):
  result = dict()
  for each in arr:
    result[each[key]] = each  # overwrite
  return result.values()

#@rediscache("api:projects2", 60*60)
def api_projects2_():
  commits = query('''
    select c.project_id, c.sloc, c.floc, c.timestamp, c.codefat, c.id
    from (select project_id, max(timestamp) as timestamp
          from commits
          where sloc > 0
          group by project_id) x, commits c
    where x.project_id = c.project_id
          and x.timestamp = c.timestamp
    ''')
  commits = remove_duplicates(commits, 'project_id')
  map_project_name(commits)
  return json.dumps(commits)

def prec(f, n):
  return int(f*n)/float(n)

@app.route('/api/project/<int:project_id>')
def api_project(project_id):
  project = get_project(project_id)
  project['branches'] = git.get_branches(project['name'])
  return jsonify(project=project)

def get_mapper(value_list, key_prop):
  key_map = dict()
  for each in value_list:
    key_map[each[key_prop]] = each
  def mapper(key):
    return key_map.get(key)
  return mapper

def get_commits_project_branch(project_id, branch):
  if project_id == '' or branch == '':
    return []
  project = get_project(project_id)
  revlist = get_rev_list(project["name"], branch)
  commits = get_commits_by_project(project_id)
  return filter(None, map(get_mapper(commits, "sha1"), revlist))

#@rediscache('api:revlist', 60*60)
def get_rev_list(project_name, branch):
  return git.rev_list(project_name, "origin/" + branch)

@app.route('/api/commits')
def api_commits():
  project_id = request.args.get('project_id', '')
  branch = request.args.get('branch', '')
  return json.dumps(get_commits_project_branch(project_id, branch))

@app.route('/api/commit/<int:project_id>/', defaults=dict(commit_id='HEAD'))
@app.route('/api/commit/<int:project_id>/<commit_id>')
def api_commit(project_id, commit_id):
  project = get_project(project_id)
  commit = get_commit(project_id, commit_id)
  filelist = git.ls_tree(get_db(), project_id, commit_id)
  diffs = git.diff_tree(get_db(), project_id, commit_id)

  status_map = dict()
  for diff in diffs:
    status_map[diff['new']['filename']] = diff['status']
  for file in filelist:
    file['status'] = status_map.get(file['name'], '')

  return jsonify(commit=commit,project=project,diffs=diffs,filelist=filelist)

@app.route('/api/diff/<int:project_id>/<sha1>/<old>/<new>')
def api_diff(project_id, sha1, old, new):
  lines = git.diff(get_db(), project_id, sha1, old, new)
  return jsonify(lines=lines)

@app.route('/api/users')
def api_users():
  return api_users_()

@rediscache("api:users", 60*60)
def api_users_():
  users = get_users()
  map_project_ids_to_projects(users)
  return jsonify(users=users)

@app.route('/api/contribution')
def api_contribution():
  project_id = request.args.get('project_id', '')
  return json.dumps(query("""select
      author,
      count(*) as no_commits,
      sum(delta_sloc) as delta_sloc,
      sum(delta_floc) as delta_floc
        from commits
        where project_id = ?
        group by author""", (project_id,)))

@app.route('/api/user/<author>')
def api_user(author):
  user = get_user(author)
  commits = get_commits_by_author(author)
  map_project_ids_to_projects([user])
  return jsonify(user=user, commits=commits)

@app.route('/api/user2')
def api_user2():
  author = request.args.get('author', '')
  commits = get_commits_by_author(author)
  profile = get_user_profile(author)
  map_project_name(profile)
  return jsonify(user=dict(author=author, profile=profile), commits=commits)

def map_project_name(arr):
  mapper = project_name_mapper()
  for each in arr:
    each['project_name'] = mapper(each['project_id'])

TimedStat = namedtuple("TimedStat", ["sloc", "floc", "timestamp"])

def tuple_sum(a, b):
  return TimedStat(a.sloc+b.sloc, a.floc+b.floc, 0)

@app.route('/api/daily')
def api_daily():
  return api_daily_()

#@rediscache("api:daily", 60*60)
def api_daily_():
  projects = get_projects()
  commits = query("select sha1, sloc, floc, timestamp from commits where sloc > 0")
  mapper = get_mapper(commits, "sha1")
  matrix = dict()
  for project in projects:
    project_id = project["id"]
    for sha1 in get_rev_list(project["name"], project["branch"]):
      commit = mapper(sha1)
      if commit is None:
        continue
      d = str(date.fromtimestamp(commit["timestamp"]))
      if d in matrix:
        day = matrix[d]
        if not project_id in day or day[project_id].timestamp < commit["timestamp"]:
          day[project_id] = TimedStat(commit["sloc"], commit["floc"], commit["timestamp"])
      else:
        matrix[d] = {project_id:TimedStat(commit["sloc"], commit["floc"], commit["timestamp"])}
  projects = dict()
  result = []
  for d in sorted(matrix.iterkeys()):
    projects.update(matrix[d])
    sloc,floc,timestamp = reduce(tuple_sum, projects.itervalues())
    codefat = 100*floc/sloc if sloc!=0 else 0
    result.append(dict(date=d,sloc=sloc,codefat=codefat))
  return json.dumps(result)

@app.route("/api/filelist")
def api_filelist():
  project_id = request.args.get('project_id', '')
  commit_id = request.args.get('commit_id', '')
  return api_filelist_(project_id, commit_id)


@rediscache("api:filelist", 60*60)
def api_filelist_(project_id, commit_id):
  filelist = git.ls_tree(get_db(), project_id, commit_id)
  return json.dumps(filelist)
