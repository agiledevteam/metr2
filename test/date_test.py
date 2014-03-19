import unittest
from datetime import date, timedelta
import sqlite3
from metrapp import app
from metrapp import database

class DateTestCase(unittest.TestCase):
	def setUp(self):
		self.db = sqlite3.connect(app.config['DATABASE'])

	def tearDown(self):
		self.db.close()

	def testDate(self):
		assert date(2014, 3, 17).year == 2014

	def testDateArithmetic(self):
		day = date(2014, 3, 17) - timedelta(days=17)
		assert day == date(2014, 2, 28)
