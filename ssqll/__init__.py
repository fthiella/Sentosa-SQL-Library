# -*- coding: utf-8 -*-
"""
Python Backend "Sentosa SQL Library" for DataTables and Frontend applications
"""
from werkzeug.datastructures import ImmutableDict
import re
import pprint

__version__ = "0.1"
__title__ = "Sentosa SQL Library"
__description__ = "Backend SQL Library for DataTables and Frontend applications"
__url__ = "https://github.com/fthiella"
__uri__ = __url__
__doc__ = __description__ + " <" + __uri__ + ">"
__author__ = "Federico Thiella"
__email__ = "fthiella@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2020 Federico Thiella" 

# TODO: read here later: https://python-packaging.readthedocs.io/en/latest/minimal.html

# parse Datatable Args

class __GrowingList(list):
	def __setitem__(self, index, value):
		if index >= len(self):
			self.extend([None]*(index + 1 - len(self)))
		list.__setitem__(self, index, value)

def parseDatatableArgs(args):
	p = {}
	for a in args:
		if a in ['draw', 'start', 'length']:
			p[a]=args.get(a)
		else:
			m = re.match(r'^(\w+)(?:\[(\w+)\])(?:\[(\w+)\])?(?:\[(\w+)\])?$', a)
			if m:
				g = m.groups()
				if g[0]=='search' and g[1] in ['value', 'regex'] and g[2] is None and g[3] is None:
					if 'search' not in p:
						p['search'] = {}
					p['search'][g[1]] = args.get(a)
				elif g[0]=='order' and g[1].isdigit() and g[2] in ['column','dir'] and g[3] is None:
					if 'order' not in p:
						p['order'] = __GrowingList()
					if len(p['order'])<int(g[1])+1:
						p['order'][int(g[1])]={}
					p['order'][int(g[1])][g[2]] = args.get(a)
				elif g[0]=='columns' and g[1].isdigit() and g[2] in ['data', 'name', 'searchable', 'orderable'] and g[3] is None:
					if 'columns' not in p:
						p['columns'] = __GrowingList()
					if len(p['columns'])<int(g[1])+1:
						p['columns'][int(g[1])]={}
					p['columns'][int(g[1])][g[2]] = args.get(a)
				elif g[0]=='columns' and g[1].isdigit() and g[2]=='search' and g[3] in ['value','regex']:
					if 'search' not in p['columns'][int(g[1])]:
						p['columns'][int(g[1])]['search']={}
					p['columns'][int(g[1])]['search'][g[3]]=args.get(a)
				else:
					print("{} non elaborato".format(a))
			else:
				print("{} non elaborato".format(a))

	pp = pprint.PrettyPrinter(indent=4)
	print("---\nArgs:\n\n")
	pp.pprint(args)
	print("---\nParsed:\n\n")
	pp.pprint(p)
	print("---")

	return p

# TODO: how to quote a string with quotes? or any other special characters?

DBMS_MAP = {
	'SQLite' : {
		"delimiter"  : ',',
		"quote"      : '"',
		"search_map" : {
			'='     : '{}=?',
			'like'  : '{} like ? || \'%\'',
			'ilike' : '{} like ? || \'%\'',
			'sub'   : '{} like \'%\' || ? || \'%\'',
		},
		"limit" : 'limit {0}, {1}',
	},
	'Pg' : {
		"delimiter"  : ',',
		"quote"      : '"',
		"search_map" : {
			'='     : '{}=?',
			'like'  : '{} like ? || \'%\'',
			'ilike' : '{} ilike ? || \'%\'',
			'sub'   : '{} like \'%\' || ? || \'%\'',
		},
		"limit" : 'limit {1} offset {0}',
	},
	'mysql' : {
		"delimiter"    : ',',
		"quote"      : '`',
		"search_map" : {
			'='     : '{}=?',
			'like'  : '{} like concat(?,\'%\')',
			'ilike' : '{} like concat(?,\'%\')',
			'sub'   : '{} like concat(?,\'%\')',
		},
		"limit" : 'limit {0}, {1}',
	},
	'Oracle' : {
		"delimiter" : ',',
		"quote" : '"',
		"search_map" : {
			'='     : '{}=?',
			'like'  : '{} like ? || \'%\'',
			'ilike' : 'regexp_like({}, \'^\' || ?, \'i\')',
			'sub'   : '{} like \'%\' || ? || \'%\'',
		},
		"top" : ' {columns} from (select qqq.*, rownum rrr from (select ',
		"limit" : ') qqq where rownum <= {2}) where rrr>{0}',
	}
}

class SSqll:
	"""
	Sentosa Sql Class
	Sql queries for DataTables and any other Frontend application
	"""

	def __init__(self, **kwargs):
		"""
		Sentosa Sql Class Initialization

		dbms:
		  SQLite, Pg, mysql, Oracle
		source:
		  source table, view, or query
		columns:
		  list of columns to return
		order:
		  (optional) list of columns to orer by
		filters:
		  (optional) list of columns to filter by
		move:
		  search, goto, forwards, backwards
		"""

		# TODO: check if input is okay
		self.source = kwargs['source'] if 'source' in kwargs else None
		self.columns = kwargs['columns'] if 'columns' in kwargs else None
		self.order = kwargs['order'] if 'order' in kwargs else []
		self.filters = kwargs['filters'] if 'filters' in kwargs else []
		self.limit = kwargs['limit'] if 'limit' in kwargs else None
		self.dbms = kwargs['dbms'] if 'dbms' in kwargs else None
		self.move = kwargs['move'] if 'move' in kwargs else 'search'

	def __quote(self, name: str, quote: str) -> str:
		"""returns a quoted string"""
		# TODO: in the unluky event that the column name contains special characters,
		# those special characters has to be quoted as well...
		return quote + name + quote;

	def __whereFilter(self, col: str, searchcriteria: str = "sub") -> str:
		"""
		given a column name col, the type of search searchcriteria (=, like, ilike, sub)
		returns a single where statement
		"""
		return DBMS_MAP[self.dbms]["search_map"][searchcriteria].format(
			self.__quote(
				col,
				DBMS_MAP[self.dbms]["quote"]
			))

	def __limitFilterTop(self, **kwargs):
		return DBMS_MAP[kwargs["dbms"]].get("top", "").format(
					kwargs.get("start", 0),
					kwargs.get("length", 0),
					kwargs.get("start", 0) + kwargs.get("length", 0),
					columns=", ".join(kwargs.get("columns", None))
				)

	def __limitFilterBottom(self, **kwargs):
		return DBMS_MAP[kwargs["dbms"]].get("limit", "").format(
					kwargs.get("start", 0),
					kwargs.get("length", 99),
					kwargs.get("start", 0) + kwargs.get("length", 99)
				)

	def __invertOrder(self, ord: str, inv:str) -> str:
		if ord not in ['asc','desc']:
			raise ValueError("order must be 'asc' or 'desc'")

		if inv and ord=='asc': return 'desc'
		if inv and ord=='desc': return 'asc'
		return ord

	def __conditions(self, **kwargs):
		o = { 'find': '=', 'forwards': '>', 'backwards': '<' }

		# divide filters by type: move columns vs others

		f_move   = list(filter(lambda x: x.get('type', 'search') == 'move',   kwargs['filters']))
		f_search = list(filter(lambda x: x.get('type', 'search') == 'search', kwargs['filters']))

		# calculate move filters

		m_where = []
		m_data = []

		if kwargs["move"] in ['find', 'forwards', 'backwards']:
			for i in range(len(f_move), 0, -1):
				or_where = list(map(
						lambda x: self.__whereFilter(col = x['name'], searchcriteria = '='),
						f_move[0:i-1]
						))
				# TODO: try to use whereFilter, if possible
				# o .. deve diventare searchcriteria
				or_where.append(self.__quote(f_move[i-1]['name'],DBMS_MAP[kwargs["dbms"]]['quote']) + o[kwargs["move"]] + "?")
				m_where.append('(' + ' and '.join(or_where) + ')')

				m_data.extend(list(map(lambda x: x['search'], f_move[0:i])))

				if kwargs["move"]=='find':
					break

		# calculate other filters

		s_where = [self.__whereFilter(col=x['name'], searchcriteria=x.get('searchcriteria', 'sub')) for x in f_search]
		s_data = [x['search'] for x in f_search]

		q_where = []
		if m_where:
			q_where.append("(" + " or ".join(m_where) + ")")
		if s_where:
			q_where.append("(" + " and ".join(s_where) + ")")

		return {
			'where': " and ".join(q_where),
			'value': m_data + s_data
		}

	def selectQuery(self, **kwargs):
		"""
		returns the select query (with placeholders) and the list of values that match the placeholders

		order:
		  columns and direction to order by (default to the constructor order by columns)
		"""

		more_filters = kwargs['filters'] if 'filters' in kwargs else []

		# TODO: consider both parameters passed to this function + constructor
		columns = list(
			map(
				lambda x: self.__quote(x['name'], DBMS_MAP[self.dbms]['quote']),
				filter(
#					lambda x: (x.get("type", "text") != "blob") and (x.get('visible', True)),
# FIXME: this has to be consistent with the table.html columns generator as well
					lambda x: (x.get("type", "text") != "blob"),
					self.columns)
			))

		if len(self.filters + more_filters)>0:
			q_filters = self.__conditions(
				filters=self.filters + more_filters,
				move=self.move,
				dbms=self.dbms
			)
		else:
			q_filters = None

		order_by = list(
			map(
				lambda x: self.__quote(
					x['name'],
					DBMS_MAP[self.dbms]['quote'])
					+ " "
					+ self.__invertOrder(
						x.get("order", "asc"),
						self.move=='backwards'
					),
				kwargs['order'] if 'order' in kwargs else self.order
			))

		if 'limit' in kwargs:
			limit_top = self.__limitFilterTop(
				dbms    = self.dbms,
				start   = kwargs['limit'].get("start", 0),
				length  = kwargs['limit'].get("length", 99),
				columns = columns)
			limit_bottom = self.__limitFilterBottom(
				dbms    = self.dbms,
				start   = kwargs['limit'].get("start", 0),
				length  = kwargs['limit'].get("length", 99),
				columns = columns)
		elif self.limit:
			limit_top = self.__limitFilterTop(
				dbms    = self.dbms,
				start   = self.limit.get("start", 0),
				length  = self.limit.get("length", 99),
				columns = columns)
			limit_bottom = self.__limitFilterBottom(
				dbms    = self.dbms,
				start   = self.limit.get("start", 0),
				length  = self.limit.get("length", 99),
				columns = columns)
		else:
			limit_top = ""
			limit_bottom = ""

		query  = "select{}\n".format(limit_top)
		query += ",\n".join(list(map(lambda x: "  "+x, columns))) + "\n"
		query += "from\n"
		query += "  "+self.__quote(self.source, DBMS_MAP[self.dbms]['quote'])+"\n"

		if (q_filters):
			query += "where\n"
			query += "  " + q_filters['where'] + "\n"

		if (order_by):
			query += "order by\n"
			query += "  "+ ",\n  ".join(order_by) + "\n"

		if (limit_bottom):
			query += limit_bottom + "\n"

		if (q_filters):
			return (query, q_filters['value'])
		else:
			return (query, [])
