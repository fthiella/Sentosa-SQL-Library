# filtersql

A Python library to build parameterized SQL queries from plain dicts. I use it mainly for three things:

- DataTables backends;
- cursor-based pagination (similar to how Microsoft Access works);
- as a bridge between LLM-generated JSON and the database.

Supports PostgreSQL, SQLite, MySQL and Oracle.

---

## Install

```bash
pip install filtersql
```

---

## Quick start

```python
from filtersql import Datasource

columns = [
    {'field': 'id'},
    {'field': 'first_name'},
    {'field': 'last_name'},
    {'field': 'company_name'},
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
    order   = [{'field': 'first_name', 'order': 'asc'}],
    limit   = {'start': 0, 'length': 10},
)

print(query)
# select
#   "id",
#   "first_name",
#   "last_name",
#   "company_name"
# from
#   "sample_uk"
# where
#   ("first_name" ilike '%' || ? || '%' and "last_name" ilike '%' || ? || '%')
# order by
#   "first_name" asc
# limit 10 offset 0

print(values)
# ['John', 'Smith']

rows = execute_db(query, values)
```

---

## Using filtersql with AI / LLM pipelines

The idea is simple: the LLM parses the user question and returns a JSON with the filters, Pydantic validates the structure, and filtersql builds the SQL. The values are always passed as parameters so there is no risk of SQL injection even if the model produces unexpected output.

### Basic flow

```
user question → LLM → JSON → Pydantic → filtersql → parameterized SQL
```

### Define the Pydantic schema

You tell the LLM exactly which fields and operators it can use. Anything outside the list gets rejected by Pydantic before it reaches the database.

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class SQLFilterSchema(BaseModel):
    field: Literal[
        'doc_type',
        'doc_date',
        'author',
        'title',
        'attributes->>supplier',   # JSONB path
        'attributes->>amount',     # JSONB path
    ] = Field(description="Column name or JSONB path")
    operator: Literal[
        '=', '!=', '>', '>=', '<', '<=',
        'icontains', 'istarts_with',
        'in', 'notin', 'null', 'notnull'
    ] = Field(description="Comparison operator")
    value: str = Field(description="Value to search for")

class QuerySchema(BaseModel):
    semantic_query: str = Field(description="Cleaned query for vector/FTS search")
    sql_filters: List[SQLFilterSchema] = Field(description="SQL filters")
```

### Call the LLM with structured output

```python
ai_response = ai_client.models.generate_content(
    model='gemini-flash',
    contents=user_question,
    config=GenerateContentConfig(
        system_instruction=YOUR_INTENT_PARSER_PROMPT,
        response_mime_type="application/json",
        response_schema=QuerySchema,
        temperature=0.0,
    )
)
parsed = QuerySchema.model_validate_json(ai_response.text)
```

### Build the WHERE clause

```python
from filtersql import Datasource

filters = [f.model_dump() for f in parsed.sql_filters]

ds = Datasource(
    source      = 'documents',
    columns     = columns,
    dbms        = 'Pg',
    placeholder = '%s',
    filters     = filters,
)

# if you need only the WHERE part to append to your own query:
where_clause, values = ds.whereQuery()
# → " and ("doc_type"=%s and "doc_date">=%s and "doc_date"<=%s)"
# → ['CONTRACT', '2025-01-01', '2025-12-31']

# or the full SELECT:
query, values = ds.selectQuery()
```

### A few things that help in practice

**Pass the current date in the prompt.** If you don't, the model tends to guess on things like "this year" or "recent documents" and gets it wrong.

**Give explicit value mappings.** For example tell the model that "contract" must become `doc_type = 'DB_CONTRACT'` exactly. Free-form values produce inconsistent filters.

**Separate semantic from deterministic.** Ask the model to put dates, document types and identifiers in `sql_filters`, and leave the conceptual topic in `semantic_query` for vector or full-text search. Mixing them in the embedding adds noise.

**Always add a fallback.** If the LLM call fails, fall back to empty filters and use the raw question for semantic search.

```python
try:
    parsed = QuerySchema.model_validate_json(ai_response.text)
except Exception:
    parsed = QuerySchema(semantic_query=user_question, sql_filters=[])
```

### JSONB fields and value_type

When a JSONB field contains numeric or date values, you need to tell Postgres the type explicitly or it will compare as text. Add `value_type` to the filter:

```python
{'field': 'attributes->>amount', 'operator': '>=', 'value': '10000', 'value_type': 'numeric'}
# → ("attributes"->>'amount')::numeric >= %s::numeric

{'field': 'attributes->>expiry_date', 'operator': '<=', 'value': '2025-12-31', 'value_type': 'date'}
# → ("attributes"->>'expiry_date')::date <= %s::date
```

Without the cast, `'9' > '10'` in Postgres text comparison, which gives wrong results for numeric ranges.

---

## Flask + DataTables example

```python
from filtersql import Datasource
from filtersql.utils import parseDatatableArgs

@app.route("/api/table.json")
def table_json():
    a = parseDatatableArgs(request.args)

    columns = [
        {'field': 'id'},
        {'field': 'first_name'},
        {'field': 'last_name'},
        {'field': 'company_name'},
    ]

    # build filters from DataTable per-column search
    filters = []
    for k in a['columns'].values():
        if k['search']['value']:
            col = columns[int(k['data'])]
            filters.append({
                'field':    col['field'],
                'operator': 'icontains',
                'value':    k['search']['value'],
            })

    # build order from DataTable
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

Cursor-based pagination without offset. Useful for large tables where `LIMIT x OFFSET y` gets slow, or when you need to navigate record by record like in Microsoft Access.

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

Use `move='backwards'` to go in reverse, or `move='find'` to jump to a specific record. Multi-column cursors are supported - just add more entries to `filters` with `type='move'`.

---

## Full-text search (PostgreSQL only)

Two operators for full-text search with `websearch_to_tsquery`:

`fts` - for a pre-built `tsvector` column:
```python
{'field': 'tsv_content', 'operator': 'fts', 'value': 'oxygen supply'}
# → "tsv_content" @@ websearch_to_tsquery('italian', %s)
```

`fts_query` - builds the tsvector on the fly from a text column:
```python
{'field': 'description', 'operator': 'fts_query', 'value': 'oxygen supply'}
# → to_tsvector('italian', coalesce("description", '')) @@ websearch_to_tsquery('italian', %s)
```

Default language is `italian`. You can change it:
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
| `null` / `notnull` | NULL checks (no value bound) |
| `in` / `notin` | List membership |
| `reverse_in` | Value in a set of columns - `%s IN (col1, col2)` |
| `fts` | Full-text search on tsvector column (Pg only) |
| `fts_query` | Full-text search on text column (Pg only) |

JSONB column access in PostgreSQL uses `field->>key` notation:
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
