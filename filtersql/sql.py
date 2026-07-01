# -*- coding: utf-8 -*-

DBMS_MAP = {
    'SQLite': {
        "delimiter":   ',',
        "quote":       '"',
        "search_map": {
            '=':            '{}=?',
            '!=':           '{}!=?',
            '>':            '{}>?',
            '>=':           '{}>=?',
            '<':            '{}<?',
            '<=':           '{}<=?',
            'starts_with':  '{} glob ? || \'*\'',
            'ends_with':    '{} glob \'*\' || ?',
            'contains':     '{} glob \'*\' || ? || \'*\'',
            'istarts_with': '{} like ? || \'%\'',
            'iends_with':   '{} like \'%\' || ?',
            'icontains':    '{} like \'%\' || ? || \'%\'',
            'in':           '{} in ({})',
            'notin':        '{} not in ({})',
            'reverse_in':   '{} in ({})',
            'null':         '{} is null',
            'notnull':      '{} is not null',
        },
        "limit":  'limit {0}, {1}',
    },
    'Pg': {
        "delimiter":   ',',
        "quote":       '"',
        "search_map": {
            '=':            '{}=?',
            '!=':           '{}!=?',
            '>':            '{}>?',
            '>=':           '{}>=?',
            '<':            '{}<?',
            '<=':           '{}<=?',
            'starts_with':  '{} like ? || \'%\'',
            'ends_with':    '{} like \'%\' || ?',
            'contains':     '{} like \'%\' || ? || \'%\'',
            'istarts_with': '{} ilike ? || \'%\'',
            'iends_with':   '{} ilike \'%\' || ?',
            'icontains':    '{} ilike \'%\' || ? || \'%\'',
            'in':           '{} in ({})',
            'notin':        '{} not in ({})',
            'reverse_in':   '{} in ({})',
            'null':         '{} is null',
            'notnull':      '{} is not null',
            'fts':          "{} @@ websearch_to_tsquery('italian', ?)",
            'fts_query':    "to_tsvector('italian', coalesce({}, '')) @@ websearch_to_tsquery('italian', ?)",
        },
        "limit": 'limit {1} offset {0}',
    },
    'mysql': {
        "delimiter": ',',
        "quote":     '`',
        "search_map": {
            '=':            '{}=?',
            '!=':           '{}!=?',
            '>':            '{}>?',
            '>=':           '{}>=?',
            '<':            '{}<?',
            '<=':           '{}<=?',
            'starts_with':  '{} like binary concat(?, \'%\')',
            'ends_with':    '{} like binary concat(\'%\', ?)',
            'contains':     '{} like binary concat(\'%\', ?, \'%\')',
            'istarts_with': '{} like concat(?, \'%\')',
            'iends_with':   '{} like concat(\'%\', ?)',
            'icontains':    '{} like concat(\'%\', ?, \'%\')',
            'in':           '{} in ({})',
            'notin':        '{} not in ({})',
            'reverse_in':   '{} in ({})',
            'null':         '{} is null',
            'notnull':      '{} is not null',
        },
        "limit": 'limit {0}, {1}',
    },
    'Oracle': {
        "delimiter": ',',
        "quote":     '"',
        "search_map": {
            '=':            '{}=?',
            '!=':           '{}!=?',
            '>':            '{}>?',
            '>=':           '{}>=?',
            '<':            '{}<?',
            '<=':           '{}<=?',
            'starts_with':  '{} like ? || \'%\'',
            'ends_with':    '{} like \'%\' || ?',
            'contains':     '{} like \'%\' || ? || \'%\'',
            'istarts_with': 'regexp_like({}, \'^\' || ?, \'i\')',
            'iends_with':   'regexp_like({}, ? || \'$\', \'i\')',
            'icontains':    'regexp_like({}, ?, \'i\')',
            'in':           '{} in ({})',
            'notin':        '{} not in ({})',
            'reverse_in':   '{} in ({})',
            'null':         '{} is null',
            'notnull':      '{} is not null',
        },
        "top": ' {columns} from (select qqq.*, rownum rrr from (select ',
        "limit": ') qqq where rownum <= {2}) where rrr>{0}',
    }
}

class Datasource:
    """
    Sentosa Sql Class
    Sql queries for DataTables, LLM outputs and any other Frontend application
    """

    def __init__(self, **kwargs):
        self.source = kwargs.get('source', None)
        self.raw_source = kwargs.get('raw_source', False)

        self.columns = kwargs.get('columns', None)
        self.order = kwargs.get('order', [])
        self.filters = kwargs.get('filters', [])

        # --- backwards compatibility, to be removed
        #self.columns = self.__shim_legacy_json(kwargs.get('columns', None))
        #self.order = self.__shim_legacy_json(kwargs.get('order', []))
        #self.filters = self.__shim_legacy_json(kwargs.get('filters', []))
        # ---

        self.limit = kwargs.get('limit', None)
        self.dbms = kwargs.get('dbms', None)
        self.move = kwargs.get('move', 'search')
        self.placeholder = kwargs.get('placeholder', '?')

        self.fts_language = kwargs.get('fts_language', 'italian')

        if self.dbms not in DBMS_MAP:
            raise ValueError(f"Unknown dbms '{self.dbms}'. Valid: {list(DBMS_MAP)}")

    def __shim_legacy_json(self, items):
        """
        backwards compatibility, to be removed
        """
        if not items:
            return items
            
        for item in items:
            if 'name' in item and 'field' not in item:
                item['field'] = item['name']
            if 'searchcriteria' in item and 'operator' not in item:
                item['operator'] = item['searchcriteria']
            if 'search' in item and 'value' not in item:
                item['value'] = item['search']
                
            op = item.get('operator')
            if op == 'sub':
                item['operator'] = 'contains'
            elif op == 'like':
                item['operator'] = 'starts_with'
            elif op == 'ilike':
                item['operator'] = 'icontains'
                
        return items

    def __quote(self, name: str, quote: str) -> str:
        """returns a quoted string"""
        if not name:
            raise ValueError(f"field name is missing or empty")

        if '.' in name:
            parts = name.split('.')
            return f"{parts[0]}.{quote}{parts[1]}{quote}"

        return quote + name + quote

    def __whereFilter(self, col: str, searchcriteria: str = "icontains", search_value=None, value_type: str = "text") -> str:
        """
        given a column name col, the type of search searchcriteria
        returns a single where statement
        """
        if searchcriteria not in DBMS_MAP[self.dbms]["search_map"]:
            searchcriteria = 'icontains'
            
        raw_statement = DBMS_MAP[self.dbms]["search_map"][searchcriteria]

        if searchcriteria in ['in', 'notin']:
            if not isinstance(search_value, (list, tuple)):
                search_value = [search_value] if search_value is not None else []
            
            if self.placeholder == '%s':
                raw_statement = raw_statement.replace('%', '%%')

            placeholders_str = ", ".join([self.placeholder] * len(search_value))
            raw_statement = raw_statement.format("{}", placeholders_str)

        elif searchcriteria in ['fts', 'fts_query']:
            if self.dbms not in ['Pg']:
                raise ValueError(f"Operator '{searchcriteria}' is not supported by {self.dbms}")
            raw_statement = raw_statement.replace('italian', self.fts_language)
            if self.placeholder == '%s':
                raw_statement = raw_statement.replace('%', '%%')
            raw_statement = raw_statement.replace('?', self.placeholder)

        elif searchcriteria == 'reverse_in':
            col_list = [c.strip() for c in col.split(',')]
            parsed_cols = []
            for c in col_list:
                if self.dbms == 'Pg' and '->>' in c:
                    parts = c.split('->>')
                    main_column = self.__quote(parts[0].strip(), DBMS_MAP[self.dbms]["quote"])
                    json_key = parts[1].strip()
                    parsed_cols.append(f"{main_column}->>'{json_key}'")
                else:
                    parsed_cols.append(self.__quote(c, DBMS_MAP[self.dbms]["quote"]))
            
            return f"{self.placeholder} IN ({', '.join(parsed_cols)})"
            
        else:
            if self.placeholder == '%s':
                raw_statement = raw_statement.replace('%', '%%')
            raw_statement = raw_statement.replace('?', self.placeholder)

        # gestione campi json con tipizzazione esplicita
        if self.dbms == 'Pg' and '->>' in col:
            parts = col.split('->>')
            main_column = self.__quote(parts[0].strip(), DBMS_MAP[self.dbms]["quote"])
            json_key = parts[1].strip()
            
            # Eseguiamo il cast guidato esplicitamente dall'attributo del JSON
            if value_type == 'numeric':
                sql_field = f"({main_column}->>'{json_key}')::numeric"
                raw_statement = raw_statement.replace(self.placeholder, f"{self.placeholder}::numeric")
            elif value_type == 'date':
                sql_field = f"({main_column}->>'{json_key}')::date"
                raw_statement = raw_statement.replace(self.placeholder, f"{self.placeholder}::date")
            else:
                sql_field = f"{main_column}->>'{json_key}'"
                
            return raw_statement.format(sql_field)

        return raw_statement.format(self.__quote(col, DBMS_MAP[self.dbms]["quote"]))

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

    def __invertOrder(self, ord: str, inv: str) -> str:
        if ord not in ['asc', 'desc']:
            raise ValueError("order must be 'asc' or 'desc'")

        if inv:
            return 'desc' if ord == 'asc' else 'asc'
        return ord

    def __conditions(self, **kwargs):
        o = {'find': '=', 'forwards': '>', 'backwards': '<'}

        f_move = list(filter(lambda x: x.get('type', 'search') == 'move',   kwargs['filters']))
        f_search = list(filter(lambda x: x.get('type', 'search') == 'search', kwargs['filters']))

        m_where = []
        m_data = []

        if kwargs["move"] in ['find', 'forwards', 'backwards']:
            for i in range(len(f_move), 0, -1):
                or_where = list(map(
                        lambda x: self.__whereFilter(col=x.get('field'), searchcriteria='='),
                        f_move[0:i-1]
                        ))
                
                m_statement = self.__quote(f_move[i-1].get('field'), DBMS_MAP[kwargs["dbms"]]['quote']) + o[kwargs["move"]] + self.placeholder
                or_where.append(m_statement)
                m_where.append('(' + ' and '.join(or_where) + ')')

                m_data.extend(list(map(lambda x: x.get('value'), f_move[0:i])))

                if kwargs["move"] == 'find':
                    break

        s_where = []
        s_data = []

        for x in f_search:
            colonna = x.get('field')
            criterio = x.get('operator', 'icontains')
            valore = x.get('value')
            tipo_valore = x.get('value_type', 'text') 

            if criterio in ['null', 'notnull']:
                s_where.append(self.__whereFilter(col=colonna, searchcriteria=criterio, search_value=valore, value_type=tipo_valore))
                continue

            if criterio in ['in', 'notin']:
                if isinstance(valore, (list, tuple)):
                    s_data.extend(valore)
                else:
                    s_data.append(valore)
            else:
                s_data.append(valore)

            s_where.append(self.__whereFilter(col=colonna, searchcriteria=criterio, search_value=valore, value_type=tipo_valore))

        q_where = []
        if m_where:
            q_where.append("(" + " or ".join(m_where) + ")")
        if s_where:
            q_where.append("(" + " and ".join(s_where) + ")")

        return {
            'where': " and ".join(q_where),
            'value': m_data + s_data
        }

    def whereQuery(self, **kwargs):
        more_filters = kwargs.get('filters', [])
        all_filters = self.filters + more_filters

        if len(all_filters) > 0:
            q_filters = self.__conditions(
                filters=all_filters,
                move=self.move,
                dbms=self.dbms
            )
            return " and " + q_filters['where'], q_filters['value']
        return "", []

    def limitPoolQuery(self, default_pool_size=40):
        return "\n" + DBMS_MAP[self.dbms].get("limit", "").format(0, default_pool_size)

    def paginateResults(self, final_list, **kwargs):
        start = kwargs.get('start', self.limit.get('start', 0) if self.limit else 0)
        length = kwargs.get('length', self.limit.get('length', 5) if self.limit else 5)
        return final_list[start : start + length]

    def selectQuery(self, **kwargs):
        more_filters = kwargs.get('filters', [])

        columns = list(
            map(
                lambda x: self.__quote(x.get('field'), DBMS_MAP[self.dbms]['quote']),
                filter(
                    lambda x: (x.get("type", "text") != "blob"),
                    self.columns)
            ))

        if len(self.filters + more_filters) > 0:
            q_filters = self.__conditions(
                filters=self.filters + more_filters,
                move=self.move,
                dbms=self.dbms
            )
        else:
            q_filters = None

        order_by = list(
            map(
                lambda x: self.__quote(x.get('field'), DBMS_MAP[self.dbms]['quote'])
                    + " "
                    + self.__invertOrder(
                        x.get("order", "asc"),
                        self.move == 'backwards'
                    ),
                kwargs.get('order', self.order)
            ))

        limit_top = ""
        limit_bottom = ""
        active_limit = kwargs.get('limit', self.limit)

        if active_limit:
            limit_top = self.__limitFilterTop(dbms=self.dbms, start=active_limit.get("start", 0), length=active_limit.get("length", 99), columns=columns)
            limit_bottom = self.__limitFilterBottom(dbms=self.dbms, start=active_limit.get("start", 0), length=active_limit.get("length", 99), columns=columns)

        query = "select{}\n".format(limit_top)
        query += ",\n".join(list(map(lambda x: "  "+x, columns))) + "\n"
        query += "from\n"
        
        if self.raw_source:
            query += "  " + self.source + "\n"
        else:
            query += "  " + self.__quote(self.source, DBMS_MAP[self.dbms]['quote']) + "\n"

        if (q_filters):
            query += "where\n"
            query += "  " + q_filters['where'] + "\n"

        if (order_by):
            query += "order by\n"
            query += "  " + ",\n  ".join(order_by) + "\n"

        if (limit_bottom):
            query += limit_bottom + "\n"

        if (q_filters):
            return (query, q_filters['value'])
        else:
            return (query, [])