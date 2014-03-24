from flask import jsonify, json, request
from datetime import datetime, date, timedelta
import time
from redis import Redis
import pickle
# metr
from metrapp import app
from metrapp.views import Project, get_db
import git
from metrapp.views import summary
from database import *
from collections import OrderedDict
from itertools import izip

redis = Redis()
API_PROJECTS_KEY = 'api:projects'

@app.route('/api/projects')
def api_projects():
  result = redis.get(API_PROJECTS_KEY)
  if result == None:
    projects = Project.all()
    data = [p.as_dict() for p in projects]
    result = json.dumps(dict(projects=data, summary=summary(projects)))
    redis.set(API_PROJECTS_KEY, result)
    redis.expire(API_PROJECTS_KEY, 3600)
  return result

@app.route('/api/projects2')
def api_projects2():
  result = query('''
    select p.id, p.name, x.sloc, x.floc, x.codefat, x.timestamp
    from projects p, 
         (select project_id as id, sloc, floc, codefat, max(timestamp) as timestamp
          from commits 
          where sloc > 0 group by project_id) x 
    where p.id = x.id
    order by p.name''')
  return json.dumps(result)

def prec(f, n):
  return int(f*n)/float(n)

@app.route('/api/project/<int:project_id>')
def api_project(project_id):
  project = Project.get(project_id)
  commits = get_commits_by_project(project_id)
  return jsonify(project=project.as_dict(), commits=commits, summary=summary([project]))

@app.route('/api/commit/<int:project_id>/', defaults=dict(sha1='HEAD'))
@app.route('/api/commit/<int:project_id>/<sha1>')
def api_commit(project_id, sha1):
  project = get_project(project_id)
  commit = get_commit(project_id, sha1)
  diffs = git.diff_tree(get_db(), project_id, sha1)
  return jsonify(commit=commit,project=project,diffs=diffs)

@app.route('/api/diff/<int:project_id>/<sha1>/<old>/<new>')
def api_diff(project_id, sha1, old, new):
  lines = git.diff(get_db(), project_id, sha1, old, new)
  return jsonify(lines=lines)

@app.route('/api/users')
def api_users():
  users = get_users()
  map_project_ids_to_projects(users)
  return jsonify(users=users)

@app.route('/api/user/<author>')
def api_user(author):
  user = get_user(author)
  commits = get_commits_by_author(author)
  map_project_ids_to_projects([user])
  return jsonify(user=user, commits=commits)

@app.route('/api/trend')
def api_trend():
  # all project
  cur = get_db().execute('select id from projects order by name')
  project_ids = [row[0] for row in cur.fetchall()]

  now = datetime.now()
  stats = [metr_day_projects(day, project_ids) for day in range(90)]
  return jsonify(result=stats)

@app.route('/api/daily')
def api_daily():
  project_id = request.args.get('project_id', '')

  def tuple_sum(a, b):
    return (a[0]+b[0], a[1]+b[1])
  def where_clause():
    if project_id == '':
      return ''
    else:
      return ' where project_id = ?'
  def where_params():
    if project_id == '':
      return []
    else:
      return [project_id]
  
  matrix = dict()
  for pid, date, sloc, floc in get_db().execute('''select 
    project_id as pid, date(timestamp, 'unixepoch') as date, sloc, floc
    from daily''' + where_clause(), where_params()):
    if date in matrix:
      matrix[date][pid] = (sloc, floc)
    else:
      matrix[date] = {pid:(sloc,floc)}
  projects = dict()
  result = []
  for date in sorted(matrix.iterkeys()):
    projects.update(matrix[date])
    sloc,floc = reduce(tuple_sum, projects.itervalues())
    codefat = 100*floc/sloc if sloc!=0 else 0
    result.append(dict(date=date,sloc=sloc,codefat=codefat))
  return json.dumps(result)


def metr_day_project(by_when, project_id):
  "return (sloc, floc)"
  def update():
    cur = get_db().execute('select sloc, floc from commits where project_id = ? and timestamp < ? and sloc > 0 order by timestamp desc limit 1', [project_id, by_when])
    row = cur.fetchone()
    if row != None and row[0] > 0: 
      return (row[0], row[1])
    else:
      return (0, 0)

  key = "codefat:%d:%d" % (project_id, by_when) 

  if redis.exists(key):
    return pickle.loads(redis.get(key))    
  else:
    result = update()
    redis.set(key, pickle.dumps(result))
    return result

def metr_day_projects(day, project_ids):
  "return (day, codefat, sloc)"
  by_day = date.today() + timedelta(days = 1 - day)
  by_when = time.mktime(by_day.timetuple())
  
  sloc = 0
  floc = 0
  for project_id in project_ids:
    sloc0, floc0 = metr_day_project(by_when, project_id)
    sloc += sloc0
    floc += floc0

  if sloc == 0:
    return (-day, 0, 0)
  else:
    return (-day, 100 * (floc/sloc), sloc)
