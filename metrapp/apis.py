from flask import jsonify
from datetime import datetime, date, timedelta
import time
from redis import Redis
import pickle
# metr
from metrapp import app
from metrapp.views import Project, get_db
import git

@app.route('/api/projects')
def api_projects():
  data = [p.__dict__ for p in Project.all()]
  return jsonify(result=data)

@app.route('/api/project/<int:project_id>')
def api_project(project_id):
  # rev-list --first-parent (for better trend viewing)
  revs = git.rev_list_first_parent(get_db(), project_id)
  # gather commits
  cur = get_db().execute('select sha1, timestamp, codefat, sloc from commits where project_id = ?', [project_id])
  commits = [(timestamp, codefat, sloc, sha1) for sha1, timestamp, codefat, sloc in cur.fetchall() if sha1 in revs]
  return jsonify(commits)

@app.route('/api/commit/<int:project_id>/', defaults=dict(sha1='HEAD'))
@app.route('/api/commit/<int:project_id>/<sha1>')
def api_commit(project_id, sha1):
  commit = git.get_commit(get_db(), project_id, sha1)
  return jsonify(result=commit)

@app.route('/api/trend')
def api_trend():
  # all project
  cur = get_db().execute('select id from projects order by name')
  project_ids = [row[0] for row in cur.fetchall()]

  now = datetime.now()
  stats = [metr_day_projects(day, project_ids) for day in range(90)]
  return jsonify(result=stats)

redis = Redis()

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
