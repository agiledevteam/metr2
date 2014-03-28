from flask import Flask
from celery import Celery

app = Flask(__name__)
app.config.from_object('metrapp.default_settings')
app.config.from_object('config')

# celery integration
def make_celery(app):
	celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
	celery.conf.update(app.config)
	TaskBase = celery.Task
	class ContextTask(TaskBase):
		abstract = True
		def __call__(self, *args, **kwargs):
			with app.app_context():
				return TaskBase.__call__(self, *args, **kwargs)
	celery.Task = ContextTask
	return celery

app.config.update(
	CELERY_BROKER_URL="redis://localhost:6379",
	CELERY_RESULT_BACKEND="redis://localhost:6379"
)

celery = make_celery(app)

import metrapp.views
import metrapp.apis
import metrapp.tasks