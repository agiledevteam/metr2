import sqlite3
from flask import g

from metrapp import app
import git

def connect_db():
  db = sqlite3.connect(app.config['DATABASE'])
  return db

def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g.db = connect_db()
  return db

@app.teardown_request
def teardown_request(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()

def get_projects():
  cur = get_db().execute('select id, name from projects order by name')
  return [make_dict(cur, row) for row in cur.fetchall()]

def get_project(project_id):
  cur = get_db().execute('select id, name from projects where id = ?', (project_id,))
  return make_dict(cur, cur.fetchone())

def get_user(author):
  cur = get_db().execute("""select 
      author, 
      count(*) as no_commits, 
      group_concat(project_id, " ") as project_ids, 
      sum(delta_sloc) as sum_delta_sloc, 
      sum(delta_floc) as sum_delta_floc
        from commits 
        where author = ?""",
        [author])
  return make_dict(cur, cur.fetchone())

def map_project_ids_to_projects(users):
  projects = get_projects()
  all_projects = dict()
  for project in projects:
    all_projects[project['id']] = project
  for user in users:
    project_ids = user['project_ids']
    user['projects'] = [all_projects[int(project_id)] for project_id in set(project_ids.split())]

def get_users():
  cur = get_db().execute("""select 
      author, 
      count(*) as no_commits, 
      group_concat(project_id, " ") as project_ids, 
      sum(delta_sloc) as sum_delta_sloc, 
      sum(delta_floc) as sum_delta_floc
        from commits 
        group by author""")
  return [make_dict(cur, row) for row in cur.fetchall()]

def get_commits_by_project(project_id):
  cur = get_db().execute("""select
      c.sha1,
      c.author,
      p.name as project_name, 
      p.id as project_id,
      c.sloc, c.delta_sloc, c.floc, c.delta_floc, c.codefat, c.delta_codefat, 
      c.timestamp, c.parents, c.message
          from projects p,commits c
          where c.project_id = p.id and c.project_id = ? order by c.timestamp desc""",
          [project_id])
  return [make_commit(cur, row) for row in cur.fetchall()]

def get_last_successful_commit_by_project(project_id):
  ''' returns list of commit(dict).'''
  cur = get_db().execute("""select
      c.sha1, 
      c.author,
      p.name as project_name, 
      p.id as project_id,
      c.sloc, c.delta_sloc, c.floc, c.delta_floc, c.codefat, c.delta_codefat, 
      c.timestamp, c.parents, c.message
          from projects p,commits c
          where c.project_id = p.id and c.project_id = ? and c.sloc > 0 order by c.timestamp desc limit 1""",
          [project_id])
  return make_commit(cur, cur.fetchone())

def get_commits_by_author(author):
  cur = get_db().execute("""select
      c.sha1,
      c.author,
      p.name as project_name, 
      p.id as project_id,
      c.sloc, c.delta_sloc, c.floc, c.delta_floc, c.codefat, c.delta_codefat, 
      c.timestamp, c.parents, c.message 
          from projects p,commits c
          where c.project_id = p.id and c.author = ? order by c.timestamp desc""",
          [author])
  return [make_commit(cur, row) for row in cur.fetchall()]

def get_commit(project_id, sha1):
  sha1 = git.resolve(get_db(), project_id, sha1)
  cur = get_db().execute("""select 
      c.sha1,
      c.author,
      p.name as project_name, 
      p.id as project_id,
      c.sloc, c.delta_sloc, c.floc, c.delta_floc, c.codefat, c.delta_codefat, 
      c.timestamp, c.parents, c.message
          from projects p,commits c
          where c.project_id = p.id and c.project_id = ? and c.sha1 = ?""", 
          [project_id, sha1])
  row = cur.fetchone()
  return make_commit(cur, row)

def make_commit(cur, row):
  if row == None:
    return None
  commit = make_dict(cur, row)
  commit['sloc'] = safe(commit['sloc'], 0)
  commit['delta_sloc'] = safe(commit['delta_sloc'], 0)
  commit['floc'] = safe(commit['floc'], 0)
  commit['delta_floc'] = safe(commit['delta_floc'], 0)
  commit['codefat'] = safe(commit['codefat'], 0)
  commit['delta_codefat'] = safe(commit['delta_codefat'], 0)
  commit['parents'] = safe(commit['parents'], '').split() 
  commit['merge'] = len(commit['parents']) > 1
  message = commit['message']
  if len(message.splitlines()) > 0:
    commit['title'] = message.splitlines()[0].strip()
  else:
    commit['title'] = commit['sha1']
  return commit

def make_dict(cursor, row):
  return dict((cursor.description[idx][0], value) 
      for idx, value in enumerate(row))

def safe(val, default_value):
  return val if val != None else default_value
