from flask import Flask
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object('metrapp.default_settings')
app.config.from_object('config')
Bootstrap(app)

import metrapp.views
import metrapp.apis
