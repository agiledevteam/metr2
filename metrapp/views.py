from metrapp import app
from flask import send_file
from datetime import datetime, date, timedelta
import git
from database import *

@app.route('/')
def ng_root():
  return send_file("templates/ng_index.html")

class Project(object):
  def __init__(self, id, name):
    self.id = id
    self.name = name
    self.commit = get_last_successful_commit_by_project(id)

  def as_dict(self):
    return dict(id=self.id, name=self.name,
      last_update=self.last_update, codefat=self.codefat,
      sloc=self.sloc)

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
  return "ok"

@app.route('/updateall')
def update_repositories():
  for p in Project.all():
    print(p.name)
    git.update(get_db(), p.id)
  return "ok"

@app.route('/delete/<int:project_id>')
def delete(project_id):
  git.delete(get_db(), project_id)
  return "ok"
