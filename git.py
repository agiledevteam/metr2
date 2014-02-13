import app
from subprocess import call
from os import path
import config

def update(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?', [project_id])
  r = cur.fetchone()
  update_project(r[1],r[2],r[3])

def update_project(name, repo, branch):
  print name, repo, branch
  repository = repo.split("//")
  repository = repository[0] + "//" + config.SSH_USERNAME + "@" + repository[1]
  call(["git","clone",repository,"-b",branch,path.join(app.GITDIR,name)])
