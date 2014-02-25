from flask import Flask
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object('metrapp.default_settings')
Bootstrap(app)

import metrapp.views

