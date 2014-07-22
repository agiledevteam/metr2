from metrapp import app
from flask import send_file, redirect, request
from datetime import datetime, date, timedelta
import git
from database import *
import tasks

@app.route('/')
def ng_root():
  return send_file("templates/ng_index.html")

@app.route('/update/<int:project_id>')
def update(project_id):
  git.update(get_db(), project_id)
  return "ok"

@app.route('/updateall')
def update_repositories():
  tasks.update_all.queue();
  return "ok"

@app.route('/delete/<int:project_id>')
def delete(project_id):
  git.delete(get_db(), project_id)
  return "ok"

@app.route('/project')
def project():
  refspec = request.args.get('git', '')
  if refspec is '':
  	return redirect('/')
  projects = find_project(refspec)
  if len(projects) != 1:
  	return redirect('/')
  return redirect("#/project/%d" % (projects[0],))
