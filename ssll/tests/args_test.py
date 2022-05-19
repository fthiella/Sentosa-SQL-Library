import sys
sys.path.append("..\\..")
import ssll.utils

import unittest
import re
import os

from pprint import pprint

cases = [
# first
[{
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
},
{
    'columns': {
        0: {'data': '0', 'name': '', 'orderable': 'true', 'search': {'regex': 'false', 'value': ''}, 'searchable': 'true'},
        1: {'data': '1', 'name': '', 'orderable': 'true', 'search': {'regex': 'false', 'value': ''}, 'searchable': 'true'},
        2: {'data': '2', 'name': '', 'orderable': 'true', 'search': {'regex': 'false', 'value': ''}, 'searchable': 'true'},
        3: {'data': '3', 'name': '', 'orderable': 'true', 'search': {'regex': 'false', 'value': ''}, 'searchable': 'true'}
    },
    'draw': '1',
    'length': '10',
    'order': {
        0: {'column': '0', 'dir': 'asc'}
    },
    'search': {'regex': 'false', 'value': ''},
    'start': '0',
    '_': '1652600072328'
}],

]

class TestArgs(unittest.TestCase):

    def test_records(self):
        for c in cases:
            a_parsed = ssll.utils.parseDatatableArgs(c[0])
            self.assertEqual(a_parsed, c[1])

if __name__ == '__main__':
    unittest.main()
