from metrapp import app
from views import connect_db
from contextlib import closing
import migrate

def init_db():
  with closing(connect_db()) as db:
    migrate.init(db)
