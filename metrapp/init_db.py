from metrapp import app
from views import connect_db
from contextlib import closing
import metrdb

def init_db():
  with closing(connect_db()) as db:
    metrdb.init(db)
