from metrapp import celery, app
from sh import git, pwd
import redis
import pickle


@celery.task()
def add_together(a, b):
	return a + b

@celery.task()
def task_clone(name, repositoryUrl):
	try:
		print(pwd())
	except:
		pass
