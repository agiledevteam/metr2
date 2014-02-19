import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort,\
  render_template, flash, jsonify
from flask_bootstrap import Bootstrap
from contextlib import closing
from datetime import datetime
import time

import git
import config # check if config.py is prepared

DATABASE = 'metr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
GITDIR = 'git'

app = Flask(__name__)
app.config.from_object(__name__)
Bootstrap(app)

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

def init_db():
  with closing(connect_db()) as db:
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()

def last_commit(id):
  try:
    cur = g.db.execute('select id, timestamp, sloc, dloc, cc from commits where project_id=? order by timestamp desc limit 1', [id])
    row = cur.fetchone()
    return dict(id=row[0], timestamp=row[1], sloc=row[2], dloc=row[3], cc=row[4])
  except:
    return None 

@app.route('/')
def show_projects():
  return render_template('show_projects.html', projects=Project.all())

@app.route('/users')
def show_users():
  return render_template('show_projects.html', projects=Project.all())

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

@app.template_filter('datetime')
def filter_datetime(timestamp):
  d = datetime.fromtimestamp(timestamp)
  return d.ctime()

if __name__ == '__main__':
  app.run()

