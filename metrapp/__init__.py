from flask import Flask

app = Flask(__name__)
app.config.from_object('metrapp.default_settings')
app.config.from_object('config')

import metrapp.views
import metrapp.apis
