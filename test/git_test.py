import unittest
import metrdb
import sqlite3
import git

class GitTest(unittest.TestCase):
	def setUp(self):
		self.db = sqlite3.connect(':memory:')
		metrdb.init(self.db)

	def testUpdateDailyWhenInsertCommit(self):
		t1 = 1395154800
		git.insert_commit(self.db, 1, git.Commit('abc', 'author', t1, 'message', 'parents', 10, 1, 10))

		cur = self.db.execute('select project_id, timestamp, sloc, floc from daily')
		rows = [row for row in cur.fetchall()]
		assert len(rows) == 1
		assert rows[0][1] == t1

		# insert older commit
		git.insert_commit(self.db, 1, git.Commit('abc', 'author', t1-1, 'message', 'parents', 20, 2, 10))

		cur = self.db.execute('select project_id, timestamp, sloc, floc from daily')
		rows = [row for row in cur.fetchall()]
		assert len(rows) == 1
		assert rows[0][1] == t1

		# insert newer commit
		git.insert_commit(self.db, 1, git.Commit('abc', 'author', t1+1, 'message', 'parents', 30, 3, 10))

		cur = self.db.execute('select project_id, timestamp, sloc, floc from daily')
		rows = [row for row in cur.fetchall()]
		assert len(rows) == 1
		assert rows[0][1] == t1+1

	def testUpdateItsOwnDeltaWhenInsertGivenParent(self):
		"""update delta if this commits is successful (sloc > 0)
		  1. if there are children already? then update children's delta
		  2. if there is a single parent already? then update its own delta
		  """
		t1 = 1395154800
		git.insert_commit(self.db, 1, git.Commit('c0', 'author', t1-1, 'message', '', 12, 3, 25))

		# insert child
		git.insert_commit(self.db, 1, git.Commit('c1', 'author', t1, 'message', 'c0', 10, 1, 10))

		cur = self.db.execute('select delta_sloc, delta_floc, delta_codefat from commits where sha1=?', ('c1',))
		row = cur.fetchone()
		assert row == (-2, -2, -15)

	def testUpdateChildrensDeltaWhenInsertGivenChildren(self):
		"""update delta if this commits is successful (sloc > 0)
		  1. if there are children already? then update children's delta
		  2. if there is a single parent already? then update its own delta
		  """
		t1 = 1395154800
		git.insert_commit(self.db, 1, git.Commit('c1', 'author', t1, 'message', 'c0', 10, 1, 10))
		git.insert_commit(self.db, 1, git.Commit('c2', 'author', t1, 'message', 'c0', 12, 3, 25))

		# insert parent
		git.insert_commit(self.db, 1, git.Commit('c0', 'author', t1-1, 'message', '', 25, 5, 20))

		cur = self.db.execute('select delta_sloc, delta_floc, delta_codefat from commits where sha1=?', ('c1',))
		row = cur.fetchone()
		assert row == (-15, -4, -10)
		cur = self.db.execute('select delta_sloc, delta_floc, delta_codefat from commits where sha1=?', ('c2',))
		row = cur.fetchone()
		assert row == (-13, -2, 5)

