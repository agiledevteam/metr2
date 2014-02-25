from metrapp import app

import sqlite3
from flask import request, session, g, redirect, url_for, abort,\
  render_template, flash, jsonify
from contextlib import closing
from datetime import datetime, date, timedelta
import time
import git


@app.before_request
def before_request():
  g.db = connect_db()

class Closer(object):
  def close(self): pass

@app.teardown_request
def teardown_request(exception):
  db = getattr(g, 'db', Closer())
  db.close()

def connect_db():
  return sqlite3.connect(app.config['DATABASE'])

def last_commit(project_id):
  try:
    cur = g.db.execute('select id, timestamp, sloc, dloc from commits where project_id=? order by timestamp desc limit 1', [project_id])
    row = cur.fetchone()
    return dict(id=row[0], timestamp=row[1], sloc=row[2], dloc=row[3])
  except:
    return None 

@app.route('/')
def show_projects():
  projects=Project.all()
  def summary():
    sloc = 0
    dloc = 0
    for p in projects:
      sloc0, dloc0 = p.metr() 
      sloc += sloc0
      dloc += dloc0
    codefat = 100 * (1 - dloc/sloc)
    codefat_s = "%.2f" % codefat
    codefat_i, codefat_f = codefat_s.split(".")
    return dict(codefat_i=codefat_i,codefat_f=codefat_f,total_sloc=sloc)
  return render_template('show_projects.html',projects=projects,summary=summary())

class User(object):
  def __init__(self, email, no_commits, projects):
    self.email = email
    self.no_commits = no_commits
    self.projects = projects

@app.route('/users')
def show_users():
  cur = g.db.execute('select id, name from projects order by name')
  all_projects = dict()
  for row in cur.fetchall():
    all_projects[row[0]] = dict(id=row[0], name=row[1]) 

  cur = g.db.execute('select author, count(*), group_concat(project_id, " ") from commits group by author')
  users = []
  for row in cur.fetchall():
    email = row[0]
    no_commits = row[1]
    projects = [all_projects[int(project_id)] for project_id in set(row[2].split())]
    users.append(User(email, no_commits, projects))
  return render_template('show_users.html', users=users)

@app.route('/add', methods=['POST'])
def add_project():
  if not session.get('logged_in'):
    abort(401)
  g.db.execute('insert into projects (name, repository, branch) values (?, ?, ?)',
    [request.form['name'], request.form['repository'], request.form['branch']])
  g.db.commit()
  flash('New project was successfully added')
  return redirect(url_for('show_projects'))

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
      return redirect(url_for('show_projects'))
  return render_template('login.html', error=error)

@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  flash('You were logged out')
  return redirect(url_for('show_projects'))

@app.route('/clone')
def clone_repositories():
  flash('Not implemented')
  return redirect(url_for('show_projects'))

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
      return '%.2f%%' % ((1 - self.commit['dloc']/self.commit['sloc']) * 100)
    else:
      return "--"

  def metr(self):
    if self.commit != None:
      return (self.commit['sloc'], self.commit['dloc'])
    else:
      return (0, 0)
    
  @property
  def sloc(self):
    if self.commit != None and self.commit['sloc'] != 0:
      return self.commit['sloc']
    else:
      return "--"

  def commits(self, limit = 20):
    cur = g.db.execute('select sha1, author, timestamp, dloc, sloc from commits where project_id = ? order by timestamp desc limit ?', [self.id, limit])
    return [dict(id=row[0], author=row[1], timestamp=row[2], dloc=row[3], sloc=row[4]) for row in cur.fetchall() if row[2] > 0]

  @staticmethod
  def get(project_id):
    cur = g.db.execute('select id, name from projects where id = ? limit 1', [project_id])
    row = cur.fetchone()
    return Project(id=row[0], name=row[1])

  @staticmethod
  def all():
    cur = g.db.execute('select id, name from projects order by name')
    projects = [Project(id=row[0], name=row[1]) for row in cur.fetchall()]
    return projects
  
  @staticmethod
  def user_projects(author):
    cur = g.db.execute('select project_id from commits where author = ? group by project_id',[author])
    project_id = [ row[0] for row in cur.fetchall() ]
    projects = [ Project.get(i) for i in project_id ]
    return projects     

@app.route('/project/<int:project_id>')
def project(project_id):
  project = Project.get(project_id)
  return render_template('project.html', project=project,commits=project.commits(20))

@app.route('/update/<int:project_id>')
def update(project_id):
  git.update(g.db, project_id)
  return redirect(url_for('show_projects'))

@app.route('/updateall')
def update_repositories():
  for p in Project.all():
    git.update(g.db, p.id)
  return redirect(url_for('show_projects'))

@app.route('/delete/<int:project_id>')
def delete(project_id):
  git.delete(g.db, project_id)
  return redirect(url_for('show_projects'))

@app.route('/api/projects')
def api_projects():
  data = [p.__dict__ for p in Project.all()]
  return jsonify(result=data)

@app.route('/api/project/<int:project_id>')
def api_project(project_id):
  cur = g.db.execute('select timestamp, 100*(1-dloc/sloc), sloc from commits where project_id = ? order by timestamp', [project_id])
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
  commit = git.get_commit(g.db, project_id, sha1)
  diffs = git.diff_tree(g.db, project_id, sha1)
  return render_template('commit.html', project=project, commit=commit, diffs=diffs)
  
@app.route('/api/commit/<int:project_id>/', defaults=dict(sha1='HEAD'))
@app.route('/api/commit/<int:project_id>/<sha1>')
def api_commit(project_id, sha1):
  commit = git.get_commit(g.db, project_id, sha1)
  return jsonify(result=commit)

CACHE_DAILY = dict()

def metr_day_project(by_when, project_id):
  "return (sloc, dloc)"
  def update():
    cur = g.db.execute('select sloc, dloc from commits where project_id = ? and timestamp < ? order by timestamp desc limit 1', [project_id, by_when])
    row = cur.fetchone()
    if row != None and row[0] > 0: 
      return (row[0], row[1])
    else:
      return (0, 0)

  key = (project_id, by_when) 
  if key in CACHE_DAILY:
    return CACHE_DAILY[key]
  else:
    result = update()
    CACHE_DAILY[key] = result
    return result

def metr_day_projects(day, project_ids):
  "return (day, codefat, sloc)"
  by_day = date.today() + timedelta(days = 1 - day)
  by_when = time.mktime(by_day.timetuple())
  
  sloc = 0
  dloc = 0
  for project_id in project_ids:
    sloc0, dloc0 = metr_day_project(by_when, project_id)
    sloc += sloc0
    dloc += dloc0

  if sloc == 0:
    return (-day, 0, 0)
  else:
    return (-day, 100 * (1-dloc/sloc), sloc)

@app.route('/api/trend')
def api_trend():
  # all project
  cur = g.db.execute('select id from projects order by name')
  project_ids = [row[0] for row in cur.fetchall()]

  now = datetime.now()
  stats = [metr_day_projects(day, project_ids) for day in range(30)]
  return jsonify(result=stats)



