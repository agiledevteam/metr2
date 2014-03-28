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


	def testCommitObjectWithMergeTagObject(self):
		author, timestamp, message, parents = git.parse_commit_("""tree 79adda7cddb4432e4313dc7aa3247da9e4b4c0a2
parent b10d4c6bcfc3786bcb49876f3bc2f060df0b8f6b
parent 7422f735fc532f7a862d11805a641d1cb5e29569
author Steve Kondik <shade@chemlab.org> 1360737540 -0800
committer Steve Kondik <shade@chemlab.org> 1360737540 -0800
mergetag object 7422f735fc532f7a862d11805a641d1cb5e29569
 type commit
 tag android-4.2.2_r1
 tagger The Android Open Source Project <initial-contribution@android.com> 1360687897 -0800
 
 Android 4.2.2 release 1
 -----BEGIN PGP SIGNATURE-----
 Version: GnuPG v1.4.11 (GNU/Linux)
 
 iEYEABECAAYFAlEacxkACgkQ6K0/gZqxDnjP+wCfVAQRn7xWBxnoSK+09qJg+MMG
 kvUAnRbWjzyUD52TLKkrpf7kz4hxB1VG
 =EPUN
 -----END PGP SIGNATURE-----

Merge tag 'android-4.2.2_r1' of https://android.googlesource.com/platform/packages/apps/Browser into 1.1

Android 4.2.2 release 1""")
		assert "shade@chemlab.org" == author
		assert 1360737540 == timestamp
		assert """Merge tag 'android-4.2.2_r1' of https://android.googlesource.com/platform/packages/apps/Browser into 1.1

Android 4.2.2 release 1""" == message

