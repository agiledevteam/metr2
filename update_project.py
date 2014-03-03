from metrapp import app, views
import git
import sys

def update_project(project_id):
  with app.app_context():
    git.update(views.get_db(), project_id)

def show_projects():
  with app.app_context():
    db = views.get_db()
    cur = db.execute('select id, name from projects order by id')
    for id, name in cur.fetchall():
      print id, name
  

if __name__ == '__main__':
  if len(sys.argv) == 1:
    show_projects()
  else:
    update_project(int(sys.argv[1]))

