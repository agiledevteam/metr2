import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort,\
  render_template, flash
from flask_bootstrap import Bootstrap
from contextlib import closing
import git

DATABASE = '/tmp/metr.db'
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

class Closer:
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
    cur = g.db.execute('select timestamp from commits where project_id=? order by timestamp desc limit 1', [id])
    return cur.fetchone()[0]
  except:
    return 0

@app.route('/')
def show_projects():
  cur = g.db.execute('select id, name from projects order by id desc')
  projects = [dict(id=row[0], name=row[1], commit=last_commit(row[0])) for row in cur.fetchall()]
  return render_template('show_projects.html', projects=projects)

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

@app.route('/update/<int:project_id>')
def update(project_id):
  git.update(g.db, project_id)
  return redirect(url_for('show_projects'))

@app.route('/updateall')
def update_repositories():
  cur = g.db.execute('select id, name, repository, branch from projects order by id desc')
  for r in cur.fetchall():
    git.update_project(r[1], r[2], r[3])
  return redirect(url_for('show_projects'))

if __name__ == '__main__':
  app.run()

