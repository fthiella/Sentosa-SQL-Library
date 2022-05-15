import unittest
import re
import sqlite3

from sqlite3 import Error
import ssqll
import os

a_datatable = {
    '_':'1652600072328',
    'columns[0][data]':'0',
    'columns[0][name]':'',
    'columns[0][orderable]':'true',
    'columns[0][search][regex]':'false',
    'columns[0][search][value]':'',
    'columns[0][searchable]':'true',
    'columns[1][data]':'1',
    'columns[1][name]':'',
    'columns[1][orderable]':'true',
    'columns[1][search][regex]':'false',
    'columns[1][search][value]':'',
    'columns[1][searchable]':'true',
    'columns[2][data]':'2',
    'columns[2][name]':'',
    'columns[2][orderable]':'true',
    'columns[2][search][regex]':'false',
    'columns[2][search][value]':'',
    'columns[2][searchable]':'true',
    'columns[3][data]':'3',
    'columns[3][name]':'',
    'columns[3][orderable]':'true',
    'columns[3][search][regex]':'false',
    'columns[3][search][value]':'',
    'columns[3][searchable]':'true',
    'draw':'1',
    'length':'10',
    'order[0][column]':'0',
    'order[0][dir]':'asc',
    'search[regex]':'false',
    'search[value]':'',
    'start':'0'
}

a_expected = {
    'columns': [
        {'data': '0', 'name': '', 'orderable': 'true', 'search': {'regex': 'false', 'value': ''}, 'searchable': 'true'},
        {'data': '1', 'name': '', 'orderable': 'true', 'search': {'regex': 'false', 'value': ''}, 'searchable': 'true'},
        {'data': '2', 'name': '', 'orderable': 'true', 'search': {'regex': 'false', 'value': ''}, 'searchable': 'true'},
        {'data': '3', 'name': '', 'orderable': 'true', 'search': {'regex': 'false', 'value': ''}, 'searchable': 'true'}
    ],
    'draw': '1',
    'length': '10',
    'order': [
        {'column': '0', 'dir': 'asc'}
    ],
    'search': {'regex': 'false', 'value': ''},
    'start': '0'
}

class TestArgs(unittest.TestCase):

	def test_records(self):
		a_parsed = ssqll.parseDatatableArgs(a_datatable)

		self.assertEqual(a_parsed, a_expected)

if __name__ == '__main__':
	unittest.main()
