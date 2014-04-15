from metrapp import app
import logging

logging.basicConfig(filename='metr.log', level=logging.INFO)

app.run(debug=True)
