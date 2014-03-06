import sqlite3
from flask import request, session, g, redirect, url_for, abort,\
  render_template, flash, jsonify
from contextlib import closing
from datetime import datetime, date, timedelta

from metrapp import app
import git
from database import *

from math import ceil


PER_PAGE = 50

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)

app.jinja_env.globals['url_for_other_page'] = url_for_other_page

class Pagination(object):

  def __init__(self, page, per_page, total_count):
    self.page = page
    self.per_page = per_page
    self.total_count = total_count

  @property
  def pages(self):
    return int(ceil(self.total_count / float(self.per_page)))

  @property
  def has_prev(self):
    return self.page > 1

  @property
  def has_next(self):
    return self.page < self.pages

  def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
    last = 0
    for num in xrange(1, self.pages + 1):
      if num <= left_edge or (num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
        if last + 1 != num:
          yield None
        yield num
        last = num

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


@app.route('/project/<int:project_id>', defaults={'page': 1})
@app.route('/project/<int:project_id>/<int:page>')
def project(project_id,page):
  project = Project.get(project_id)
  def summary():
    sloc, floc = project.metr()
    codefat = 100 * (floc/sloc) if sloc != 0 else .0
    codefat_s = "%.2f" % codefat
    codefat_i, codefat_f = codefat_s.split(".")
    return dict(codefat_i=codefat_i,codefat_f=codefat_f,total_sloc=sloc,total_floc="%.2f" % floc)
  
  commits = get_commits_by_project(project_id)

  count = len(commits)
  pagination = Pagination(page, PER_PAGE, count)
  commits = commits[(page-1)*PER_PAGE:page*PER_PAGE]

  return render_template('project.html', project=project, summary=summary(), commits=commits, pagination=pagination)

@app.route('/users', defaults={'page': 1})
@app.route('/users/<int:page>')
def users(page):
  users = get_users()

  count = len(users)
  pagination = Pagination(page, PER_PAGE, count)
  users = users[(page-1)*PER_PAGE:page*PER_PAGE]
  
  map_project_ids_to_projects(users)
  return render_template('users.html', users=users, pagination=pagination)

@app.route('/user/<author>', defaults={'page': 1})
@app.route('/user/<author>/<int:page>')
def user(author, page):
  user = get_user(author)
  commits = get_commits_by_author(author)
  map_project_ids_to_projects([user])

  count = len(commits)
  pagination = Pagination(page, PER_PAGE, count)
  commits = commits[(page-1)*PER_PAGE:page*PER_PAGE]

  return render_template('user.html', user=user, commits=commits, pagination=pagination)

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
    self.commit = get_last_successful_commit_by_project(id)

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

@app.template_filter('date')
def filter_date(timestamp):
  d = date.fromtimestamp(timestamp)
  return str(d)

@app.route('/commit/<int:project_id>/<sha1>')
def commit(project_id, sha1):
  project = get_project(project_id)
  commit = get_commit(project_id, sha1)
  diffs = git.diff_tree(get_db(), project_id, sha1)
  return render_template('commit.html', project=project, commit=commit, diffs=diffs)

@app.route('/diff/<int:project_id>/<sha1>/<old>/<new>')
def diff(project_id, sha1, old, new):
  #old_lines, new_lines = git.diff(get_db(), project_id, old, new)
  old_lines, new_lines = [], []
  lines = git.diff(get_db(), project_id, sha1, old, new)
  return render_template('diff.html', lines=lines, old_lines=old_lines, new_lines=new_lines)

