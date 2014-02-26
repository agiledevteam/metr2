# -*- coding: utf-8 -*-
import unittest
import sqlite3
from metrapp import views, app, init_db

class UnicodeTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['DATABASE'] = ':memory:'
        self.db = views.connect_db()
        init_db.create_tables(self.db)

    def tearDown(self):
        self.db.close()
        
    def testInsertUnicodeCharInEmail(self):
        email = u'“jooyung.han@lge.com”'
        self.db.execute("insert into projects (name, repository, branch) values ('test', 'test', 'test')")
        self.db.execute("insert into commits (sha1, project_id, author) values ('', 0, ?)", [email])

