#!/usr/bin/env python
from metrapp import app
from worker import queue_daemon

queue_daemon(app)
