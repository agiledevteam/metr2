from metrapp import app, views, database
import git
import sys

def main(project_id, commit_id): 
  g = git.load_git(database.get_db(), project_id)
  result = git.metr_commit(commit_id, g)
  print "metr_commit=>", result

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print " ".join(sys.argv + ['project_id', 'commit_id'])
  else:
    with app.app_context():
      main(sys.argv[1], sys.argv[2])
