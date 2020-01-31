import unittest
import re
import sqlite3

from sqlite3 import Error
import ssqll
import os

columns = [
	{ 'name': 'id',           'visible': True },
	{ 'name': 'first_name',   'visible': True },
	{ 'name': 'last_name',    'visible': True },
	{ 'name': 'company_name', 'visible': True }
]

columns_order = [
	{ 'name': 'id', 'order': 'asc' }
]

columns_name = [
	{ 'name': 'id',           'visible': True },
	{ 'name': 'first_name',   'visible': True },
	{ 'name': 'last_name',    'visible': True },
	{ 'name': 'company_name', 'visible': True }
]

columns_name_order = [
	{ 'name': 'first_name', 'order': 'asc' },
	{ 'name': 'last_name',  'order': 'asc' },
]

class TestSql(unittest.TestCase):

	def test_records(self):
		script_dir = os.path.dirname(__file__)
		db_path = os.path.join(script_dir, 'sample-uk.db')
		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		q = ssqll.SSqll(
			source = 'sample_uk',
			columns = columns,
			order = columns_order,
			dbms = 'SQLite'
		)
		query, values = q.selectQuery()

		cur.execute(query, values)
		rows = cur.fetchall()
		self.assertEqual(len(rows), 500)
		conn.close()

	def test_limit(self):
		script_dir = os.path.dirname(__file__)
		db_path = os.path.join(script_dir, 'sample-uk.db')
		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		for s in range(500):
			q = ssqll.SSqll(
				source = 'sample_uk',
				columns = columns,
				order = columns_order,
				limit = { 'start': 0, 'length': s+1 },
				dbms = 'SQLite'
			)
			query, values = q.selectQuery()

			cur.execute(query, values)
			rows = cur.fetchall()
			self.assertEqual(len(rows), s+1)

		conn.close()

	def test_rows(self):
		script_dir = os.path.dirname(__file__)
		db_path = os.path.join(script_dir, 'sample-uk.db')
		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		q = ssqll.SSqll(
			source = 'sample_uk',
			columns = columns,
			order = columns_order,
			dbms = 'SQLite'
		)
		query, values = q.selectQuery()

		cur.execute(query, values)

		rows = cur.fetchall()

		for num, row in enumerate(rows, start=1):
			self.assertEqual(row[0], num)

		conn.close()

	def test_forwards(self):
		script_dir = os.path.dirname(__file__)
		db_path = os.path.join(script_dir, 'sample-uk.db')
		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		i = 0
		while True:
			q = ssqll.SSqll(
				source = 'sample_uk',
				columns = columns,
				order = columns_order,
				dbms = 'SQLite',
				filters = [{ 'name': 'id', 'search': i, 'type': 'move' }],
				move = 'forwards'
			)
			query, values = q.selectQuery()

			cur.execute(query, values)
			rows = cur.fetchall()
			if rows:
				i = rows[0][0]
			else:
				break
		self.assertEqual(i, 500)
		conn.close()

	def test_backwards(self):
		script_dir = os.path.dirname(__file__)
		db_path = os.path.join(script_dir, 'sample-uk.db')
		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		i = 501
		while True:
			q = ssqll.SSqll(
				source = 'sample_uk',
				columns = columns,
				order = columns_order,
				dbms = 'SQLite',
				filters = [{ 'name': 'id', 'search': i, 'type': 'move' }],
				move = 'backwards'
			)
			query, values = q.selectQuery()

			cur.execute(query, values)
			rows = cur.fetchall()
			if rows:
				i = rows[0][0]
			else:
				break
		self.assertEqual(i, 1)
		conn.close()

	def test_forwards_name(self):
		script_dir = os.path.dirname(__file__)
		db_path = os.path.join(script_dir, 'sample-uk.db')
		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		first_name=''
		last_name=''
		ids = set()

		while True:
			q = ssqll.SSqll(
				source = 'sample_uk',
				columns = columns_name,
				order = columns_name_order,
				dbms = 'SQLite',
				filters = [
					{ 'name': 'first_name', 'search': first_name, 'type': 'move' },
					{ 'name': 'last_name',  'search': last_name,  'type': 'move' },
					],
				move = 'forwards'
			)
			query, values = q.selectQuery()

			cur.execute(query, values)
			rows = cur.fetchall()
			if rows:
				ids.add(rows[0][0])
				first_name=rows[0][1]
				last_name=rows[0][2]
			else:
				break

		conn.close()
		self.assertEqual(len(ids), 500)

	def test_backwards_name(self):
		script_dir = os.path.dirname(__file__)
		db_path = os.path.join(script_dir, 'sample-uk.db')
		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		first_name='zz'
		last_name='zz'
		ids = set()

		while True:
			q = ssqll.SSqll(
				source = 'sample_uk',
				columns = columns_name,
				order = columns_name_order,
				dbms = 'SQLite',
				filters = [
					{ 'name': 'first_name', 'search': first_name, 'type': 'move' },
					{ 'name': 'last_name',  'search': last_name,  'type': 'move' },
					],
				move = 'backwards'
			)
			query, values = q.selectQuery()

			cur.execute(query, values)
			rows = cur.fetchall()
			if rows:
				ids.add(rows[0][0])
				first_name=rows[0][1]
				last_name=rows[0][2]
			else:
				break

		conn.close()
		self.assertEqual(len(ids), 500)

if __name__ == '__main__':
	unittest.main()
