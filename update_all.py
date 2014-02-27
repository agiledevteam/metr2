from metrapp import app
from metrapp.views import *

client = app.test_client()
client.get('/updateall')

