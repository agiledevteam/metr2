import time, threading
from metrapp import app
import git
from metrapp import database as db
from pickle import loads, dumps
from redis import Redis
import logging

logger = logging.getLogger("tasks")
logger.addHandler(logging.FileHandler('tasks.log'))

redis = Redis()

def task(f):
	def queue(*args, **kwargs):
		print("queue", f.__name__, args, kwargs)
		s = dumps((f, args, kwargs))
		redis.rpush(app.config['REDIS_QUEUE_KEY'], s)
	f.queue = queue
	return f

@task
def update_all():
	conn = db.connect_db()
	for project in db.get_projects(conn):
		update_project.queue(project['id'], project['name'])
	conn.close()

@task
def update_project(project_id, project_name):
	conn = db.connect_db()
	git.update(conn, project_id)
	conn.close()

def queue_daemon():
	while 1:
		msg = redis.blpop(app.config['REDIS_QUEUE_KEY'])
		func, args, kwargs = loads(msg[1])
		logger.info("dequeue", func.__name__, args, kwargs)
		try:
			func(*args, **kwargs)
			redis.lrem(app.config['REDIS_QUEUE_KEY'], msg[1])
		except:
			pass

def register_periodic_task(task_func, interval):
	t = threading.Timer(interval, task_func.queue)
	t.start()

if __name__ == "__main__":
	print("worker started...", app.config['REDIS_QUEUE_KEY'])
	register_periodic_task(update_all, 10 * 60) # every 10 mins
	queue_daemon()
