import os
import metrapp
from metrapp.init_db import init_db
import unittest
import tempfile

class MetrAppTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, metrapp.app.config['DATABASE'] = tempfile.mkstemp()
        metrapp.app.config['TESTING'] = True
        self.app = metrapp.app.test_client()
        init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(metrapp.app.config['DATABASE'])
    
    def test_empty_db(self):
        rv = self.app.get('/')
        assert 'No entries here so far' in rv.data

if __name__ == '__main__':
    unittest.main()