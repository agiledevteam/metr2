import app
from subprocess import call
from os import path

def update(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?', [project_id])
  r = cur.fetchone()
  update_project(r[1],r[2],r[3])

def update_project(name, repo, branch):
  print name, repo, branch
  repository = repo.split("//")
  repositoryChisun = repository[0] + "//chisun.joung@" + repository[1]
  if path.exists(path.join(app.GITDIR,name,".git")) :
     print "fetch..." + repo
     call(["git","--git-dir=" + path.join(app.GITDIR,name,".git"),"--work-tree=" + path.join(app.GITDIR,name),"fetch"])
     print "merge..."
     call(["git","--git-dir=" + path.join(app.GITDIR,name,".git"),"--work-tree=" + path.join(app.GITDIR,name),"merge","origin/LG_apps_master"]) 
     print "done fetch...merge"
  else :
     print "clone ..." + repo
     call(["git","clone",repositoryChisun,"-b",branch,path.join(app.GITDIR,name)])
     print "done clone"

def delete(db, project_id):
  cur = db.execute('select id, name, repository, branch from projects where id = ?',[project_id])
  r = cur.fetchone()
  print "delete ..." + path.join(app.GITDIR,r[1])
  call(["rm","-rf",path.join(app.GITDIR,r[1])])

