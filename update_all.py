import app

with app.app.app_context():
  app.before_request()
  app.update_repositories()
  app.teardown_request()
