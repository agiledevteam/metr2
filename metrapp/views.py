from metrapp import app

import sqlite3
from flask import request, session, g, redirect, url_for, abort,\
  render_template, flash, jsonify
from contextlib import closing
from datetime import datetime, date, timedelta
import time
import git
from redis import Redis
import pickle


# Database stuff

def connect_db():
  db = sqlite3.connect(app.config['DATABASE'])
  return db

def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g.db = connect_db()
  return db

@app.before_request
def before_request():
  get_db()

@app.teardown_request
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()


def last_commit(project_id):
  try:
    cur = get_db().execute('select id, timestamp, sloc, floc from commits where project_id=? order by timestamp desc limit 1', [project_id])
    row = cur.fetchone()
    return dict(id=row[0], timestamp=row[1], sloc=row[2], floc=row[3])
  except:
    return None 

@app.route('/')
def projects():
  projects=Project.all()
  def summary():
    sloc = 0
    floc = 0
    for p in projects:
      sloc0, floc0 = p.metr() 
      sloc += sloc0
      floc += floc0
    codefat = 100 * (floc/sloc) if sloc != 0 else .0
    codefat_s = "%.2f" % codefat
    codefat_i, codefat_f = codefat_s.split(".")
    return dict(codefat_i=codefat_i,codefat_f=codefat_f,total_sloc=sloc,total_floc="%.2f" % floc)
  return render_template('projects.html',projects=projects,summary=summary())

class User(object):
  def __init__(self, email, no_commits, projects):
    self.email = email
    self.no_commits = no_commits
    self.projects = projects

@app.route('/users')
def users():
  cur = get_db().execute('select id, name from projects order by name')
  all_projects = dict()
  for row in cur.fetchall():
    all_projects[row[0]] = dict(id=row[0], name=row[1]) 

  cur = get_db().execute('select author, count(*), group_concat(project_id, " ") from commits group by author')
  users = []
  for row in cur.fetchall():
    email = row[0]
    no_commits = row[1]
    projects = [all_projects[int(project_id)] for project_id in set(row[2].split())]
    users.append(User(email, no_commits, projects))
  return render_template('users.html', users=users)

@app.route('/add', methods=['POST'])
def add_project():
  if not session.get('logged_in'):
    abort(401)
  get_db().execute('insert into projects (name, repository, branch) values (?, ?, ?)',
    [request.form['name'], request.form['repository'], request.form['branch']])
  get_db().commit()
  flash('New project was successfully added')
  return redirect(url_for('projects'))

@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST':
    if request.form['username'] != app.config['USERNAME']:
      error = 'Invalid username'
    elif request.form['password'] != app.config['PASSWORD']:
      error = 'Invalid password'
    else:
      session['logged_in'] = True
      flash('You were loggined in')
      return redirect(url_for('projects'))
  return render_template('login.html', error=error)

@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  flash('You were logged out')
  return redirect(url_for('projects'))

@app.route('/clone')
def clone_repositories():
  flash('Not implemented')
  return redirect(url_for('projects'))

class Project(object):
  def __init__(self, id, name):
    self.id = id
    self.name = name
    self.commit = last_commit(id)

  @property
  def last_update(self):
    if self.commit != None:
      return filter_datetime(self.commit['timestamp'])
    else:
      return "--"

  @property
  def codefat(self):
    if self.commit != None and self.commit['sloc'] != 0:
      return 100*self.commit['floc']/self.commit['sloc']
    else:
      return 0

  def metr(self):
    if self.commit != None:
      return (self.commit['sloc'], self.commit['floc'])
    else:
      return (0, 0)
    
  @property
  def sloc(self):
    if self.commit != None:
      return self.commit['sloc']
    else:
      return 0 

  def commits(self, limit = 20):
    def safe(val):
      if val == None:
	return 0
      else:
	return val

    cur = get_db().execute('select sha1, author, timestamp, delta_floc, delta_sloc, delta_codefat from commits where project_id = ? order by timestamp desc limit ?', [self.id, limit])
    return [dict(sha1=row[0], author=row[1], timestamp=row[2], delta_floc=safe(row[3]), delta_sloc=safe(row[4]), delta_codefat=safe(row[5])) for row in cur.fetchall() if row[2] > 0]

  @staticmethod
  def get(project_id):
    cur = get_db().execute('select id, name from projects where id = ? limit 1', [project_id])
    row = cur.fetchone()
    return Project(id=row[0], name=row[1])

  @staticmethod
  def all():
    cur = get_db().execute('select id, name from projects order by name')
    projects = [Project(id=row[0], name=row[1]) for row in cur.fetchall()]
    return projects
  
  @staticmethod
  def user_projects(author):
    cur = get_db().execute('select project_id from commits where author = ? group by project_id',[author])
    project_id = [ row[0] for row in cur.fetchall() ]
    projects = [ Project.get(i) for i in project_id ]
    return projects     

@app.route('/project/<int:project_id>')
def project(project_id):
  project = Project.get(project_id)
  def summary():
    sloc, floc = project.metr()
    codefat = 100 * (floc/sloc) if sloc != 0 else .0
    codefat_s = "%.2f" % codefat
    codefat_i, codefat_f = codefat_s.split(".")
    return dict(codefat_i=codefat_i,codefat_f=codefat_f,total_sloc=sloc,total_floc="%.2f" % floc)
  return render_template('project.html', project=project, summary=summary(), commits=project.commits(20))

@app.route('/update/<int:project_id>')
def update(project_id):
  git.update(get_db(), project_id)
  return redirect(url_for('projects'))

@app.route('/updateall')
def update_repositories():
  for p in Project.all():
    git.update(get_db(), p.id)
  return redirect(url_for('projects'))

@app.route('/delete/<int:project_id>')
def delete(project_id):
  git.delete(get_db(), project_id)
  return redirect(url_for('projects'))

@app.route('/api/projects')
def api_projects():
  data = [p.__dict__ for p in Project.all()]
  return jsonify(result=data)

@app.route('/api/project/<int:project_id>')
def api_project(project_id):
  cur = get_db().execute('select timestamp, codefat, sloc from commits where project_id = ? order by timestamp', [project_id])
  data = dict()
  data['cols'] = [dict(label='commit', type='datetime'), 
      dict(label='code fat', type='number'), 
      dict(label='sloc', type='number')]
  data['rows'] = [dict(c=[dict(v=row[0]), dict(v=row[1]), dict(v=row[2])]) for row in cur.fetchall() if row[2] > 0]
  return jsonify(data)

@app.template_filter('float2')
def filter_float2(fvalue):
  if isinstance(fvalue, float):
    return '%.2f' % fvalue
  else:
    return "--"

@app.template_filter('datetime')
def filter_datetime(timestamp):
  d = datetime.fromtimestamp(timestamp)
  return d.ctime()

@app.route('/commit/<int:project_id>/', defaults=dict(sha1='HEAD'))
@app.route('/commit/<int:project_id>/<sha1>')
def commit(project_id, sha1):
  project = Project.get(project_id)
  commit = git.get_commit(get_db(), project_id, sha1)
  diffs = git.diff_tree(get_db(), project_id, sha1)
  return render_template('commit.html', project=project, commit=commit, diffs=diffs)
  
@app.route('/api/commit/<int:project_id>/', defaults=dict(sha1='HEAD'))
@app.route('/api/commit/<int:project_id>/<sha1>')
def api_commit(project_id, sha1):
  commit = git.get_commit(get_db(), project_id, sha1)
  return jsonify(result=commit)

redis = Redis()

def metr_day_project(by_when, project_id):
  "return (sloc, floc)"
  def update():
    cur = get_db().execute('select sloc, floc from commits where project_id = ? and timestamp < ? order by timestamp desc limit 1', [project_id, by_when])
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

@app.route('/api/trend')
def api_trend():
  # all project
  cur = get_db().execute('select id from projects order by name')
  project_ids = [row[0] for row in cur.fetchall()]

  now = datetime.now()
  stats = [metr_day_projects(day, project_ids) for day in range(30)]
  return jsonify(result=stats)

def update_delta(commit):
  project_id = commit['project_id']
  sha1 = commit['sha1']
  parents = git.get_parents(get_db(), project_id, sha1)
  for parent_id in parents:
    parent_commit = git.get_commit(get_db(), project_id, parent_id)
    commit['delta_sloc'] = 0
    commit['delta_floc'] = 0

@app.route('/user/<email>')
def user(email):
  cur = get_db().execute('select c.sha1, p.name, p.id, c.delta_sloc, c.delta_floc, c.delta_codefat, c.timestamp from commits c, projects p  where c.project_id=p.id and c.author=? order by c.timestamp desc limit 20', [email])
  commits = [dict(sha1=row[0], project_name=row[1], project_id=row[2], delta_sloc=row[3], delta_floc=row[4], delta_codefat=row[5], timestamp=row[6]) for row in cur.fetchall()]
  for commit in commits:
    update_delta(commit)
  user = dict(email=email)
  return render_template('user.html', user=user, commits=commits)


