
activate_this = '/home/buildmaster/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
metr2 = '/home/buildmaster/metr2'
if not metr2 in sys.path:
  sys.path.insert(0, metr2)

from metrapp import app as application
