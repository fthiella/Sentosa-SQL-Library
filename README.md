# Sentosa SQL Library

A small Python library that builds parameterized SQL queries for DataTables,
Access-style pagination, and AI-generated filters.
Supports PostgreSQL, SQLite, MySQL, and Oracle.

---

## Install

```bash
pip install ssll
```

---

## Quick start

```python
from ssll import Datasource

columns = [
    {'field': 'id'},
    {'field': 'first_name'},
    {'field': 'last_name'},
    {'field': 'company_name'},
]

order = [
    {'field': 'first_name', 'order': 'asc'},
    {'field': 'last_name',  'order': 'asc'},
]

filters = [
    {'field': 'first_name', 'operator': 'icontains', 'value': 'John'},
    {'field': 'last_name',  'operator': 'icontains', 'value': 'Smith'},
]

q = Datasource(
    source  = 'sample_uk',
    columns = columns,
    dbms    = 'Pg',
)

query, values = q.selectQuery(
    filters = filters,
    order   = order,
    limit   = {'start': 0, 'length': 10},
)

print(query)
#select
#  "id",
#  "first_name",
#  "last_name",
#  "company_name"
#from
#  "sample_uk"
#where
#  ("first_name" ilike '%' || ? || '%' and "last_name" ilike '%' || ? || '%')
#order by
#  "first_name" asc,
#  "last_name" asc
#limit 10 offset 0

print(values)
# ['John', 'Smith']

rows = execute_db(query, values)
```

---

## Flask + DataTables example

```python
from ssll import Datasource
from ssll.utils import parseDatatableArgs

@app.route("/api/table.json")
def table_json():
    a = parseDatatableArgs(request.args)

    columns = [
        {'field': 'id'},
        {'field': 'first_name'},
        {'field': 'last_name'},
        {'field': 'company_name'},
    ]

    # Build filters from DataTable per-column search
    filters = []
    for k in a['columns'].values():
        if k['search']['value']:
            col = columns[int(k['data'])]
            filters.append({
                'field':    col['field'],
                'operator': 'icontains',
                'value':    k['search']['value'],
            })

    # Build order from DataTable
    order = [
        {'field': columns[int(k['column'])]['field'], 'order': k['dir']}
        for k in a['order'].values()
    ]

    q = Datasource(
        source      = 'sample_uk',
        columns     = columns,
        dbms        = 'SQLite',
        placeholder = '?',
    )

    query, values = q.selectQuery()
    records_total = execute_db("select count(*) from ({}) t".format(query), values)[0][0]

    query, values = q.selectQuery(filters=filters)
    records_filtered = execute_db("select count(*) from ({}) t".format(query), values)[0][0]

    query, values = q.selectQuery(
        filters = filters,
        order   = order,
        limit   = {'start': int(request.args.get('start')), 'length': int(request.args.get('length'))},
    )
    rows = execute_db(query, values)

    return jsonify(
        draw            = int(request.args.get('draw')),
        recordsTotal    = records_total,
        recordsFiltered = records_filtered,
        data            = rows,
    )
```

---

## Access-style pagination

Cursor-based pagination that moves forwards or backwards through a result set, similar to how Microsoft Access navigates records. Useful for large tables where offset pagination is too slow.

```python
q = Datasource(
    source  = 'sample_uk',
    columns = columns,
    order   = [{'field': 'id', 'order': 'asc'}],
    dbms    = 'SQLite',
    move    = 'forwards',
    filters = [{'field': 'id', 'value': last_seen_id, 'type': 'move'}],
)

query, values = q.selectQuery()
```

Change `move` to `'backwards'` to go in reverse, or `'find'` to jump to an exact record. Multi-column cursors work too — just add more entries to `filters` with `type='move'`.

---

## AI-generated filters (PostgreSQL)

The library accepts filters as plain dicts, which makes it a natural fit for LLM outputs validated by Pydantic.

```python
# JSON produced by an LLM and validated by Pydantic:
sql_filters = [
    {'field': 'm.doc_type',        'operator': '=',         'value': 'CONTRACT'},
    {'field': 'm.doc_description', 'operator': 'icontains', 'value': 'License'},
    {'field': 'm.doc_date',        'operator': '>=',        'value': '2025-01-01'},
    {'field': 'm.doc_date',        'operator': '<=',        'value': '2025-12-31'},
]

q = Datasource(
    source      = 'my_view',
    columns     = columns,
    dbms        = 'Pg',
    placeholder = '%s',
)

query, values = q.selectQuery(filters=sql_filters)
```

### Full-text search (PostgreSQL only)

Two operators are available for PostgreSQL full-text search:

`fts` — searches against a pre-built `tsvector` column:
```python
{'field': 'tsv_content', 'operator': 'fts', 'value': 'contratti'}
# → tsv_content @@ websearch_to_tsquery('italian', %s)
```

`fts_query` — builds the tsvector on the fly from a text column:
```python
{'field': 'oggetto', 'operator': 'fts_query', 'value': 'contratti'}
# → to_tsvector('italian', coalesce("oggetto", '')) @@ websearch_to_tsquery('italian', %s)
```

The default language is `italian`. Override it at construction time:
```python
q = Datasource(..., fts_language='english')
```

---

## Filter operators

| Operator | Description |
|---|---|
| `=` `!=` `>` `>=` `<` `<=` | Comparison |
| `contains` | Case-sensitive substring (`LIKE '%x%'`) |
| `starts_with` | Case-sensitive prefix |
| `ends_with` | Case-sensitive suffix |
| `icontains` | Case-insensitive substring (`ILIKE`) |
| `istarts_with` | Case-insensitive prefix |
| `iends_with` | Case-insensitive suffix |
| `null` / `notnull` | NULL checks |
| `in` / `notin` | List membership |
| `reverse_in` | Value in a set of columns (`%s IN (col1, col2)`) |
| `fts` | Full-text search on tsvector column (Pg only) |
| `fts_query` | Full-text search on text column (Pg only) |

JSONB column access is supported in PostgreSQL using `->>`  notation in the field name:
```python
{'field': 'metadata->>status', 'operator': '=', 'value': 'active'}
```

---

## Supported databases

| DBMS | `dbms` value | Placeholder |
|---|---|---|
| PostgreSQL | `'Pg'` | `%s` |
| SQLite | `'SQLite'` | `?` |
| MySQL | `'mysql'` | `?` |
| Oracle | `'Oracle'` | `?` |

---

## License

MIT