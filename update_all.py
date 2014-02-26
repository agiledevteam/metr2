from metrapp import app
from metrapp.views import *

with app.app_context():
  before_request()
  update_repositories()
  teardown_request()
