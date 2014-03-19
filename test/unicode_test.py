# -*- coding: utf-8 -*-
import unittest
import sqlite3
from metrapp import views, app, init_db, database
import tempfile
import os

class UnicodeTest(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.app = app.test_client()
        init_db.init_db()
        self.db = database.connect_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
        
    def testInsertUnicodeCharInEmail(self):
        email = u'“jooyung.han@lge.com”'
        self.db.execute("insert into projects (name, repository, branch) values ('test', 'test', 'test')")
        self.db.execute("insert into commits (sha1, project_id, author) values ('', 0, ?)", [email])

