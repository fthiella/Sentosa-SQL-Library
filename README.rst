Sentosa SQL Library
-------------------

Quick start::

    >>> import ssqll
    >>>
    >>> columns = [
    >>>   { 'name': 'id',           'visible': True },
    >>>   { 'name': 'first_name',   'visible': True },
    >>>   { 'name': 'last_name',    'visible': True },
    >>>   { 'name': 'company_name', 'visible': True }
    >>> ]
    >>>
    >>> order = [
    >>>   { 'name': 'first_name', 'order': 'asc' },
    >>>   { 'name': 'last_name',  'order': 'asc' },
    >>> ]
    >>>
    >>> filters = [
    >>>   { 'name': 'first_name', 'search': 'John',   'type': 'search' },
    >>>   { 'name': 'last_name',  'search': 'Smith',  'type': 'search' },
    >>> ]
    >>>
    >>> q = ssqll.SSqll(
    >>>   source = 'sample_uk',
    >>>   columns = columns,
    >>>   dbms = 'SQLite',
    >>>   move = 'search'
    >>> )
    >>> query, values = q.selectQuery(
    >>>   filters = filters,
    >>>   limit = {'start': 0, 'length': 10},
    >>>   order = order
    >>> )
    >>> print(query)

    select
      "id",
      "first_name",
      "last_name",
      "company_name"
    from
      "sample_uk"
    where
      ("first_name" like '%' || ? || '%' and "last_name" like '%' || ? || '%')
    order by
      "first_name" asc,
      "last_name" asc
    limit 0, 10

    >>> print(values)
    
    ['John', 'Smith']

    >>>> rows = execute_db(query, values)

Flask backend basic example:

    @app.route("/api/table.json")
    def table_json():
    a = ssqll.parseDatatableArgs(request.args)

    columns = [
        { 'name': 'id',           'visible': True },
        { 'name': 'first_name',   'visible': True },
        { 'name': 'last_name',    'visible': True },
        { 'name': 'company_name', 'visible': True }
    ]

    # create filter from datatable search
    f = []
    for k in a['columns']:
        if k['search']['value']:
            f.append({'name': columns[int(k['data'])]['name'], 'search': k['search']['value']})

    # create odred from datatable
    o = [ {'name': columns[int(k['column'])]['name'], 'order': k['dir']} for k in a['order'] ]

    q = ssqll.SSqll(
        source = 'sample_uk',
        columns = columns,
        dbms = 'SQLite',
        move = 'search'
    )

    query, values = q.selectQuery()
    rows = execute_db("select count(*) from ({}) sqsq".format(query), values)
    recordsTotal = rows[0]

    query, values = q.selectQuery(filters = f)
    rows = execute_db("select count(*) from ({}) sqsq".format(query), values)
    recordsFiltered = rows[0]

    query, values = q.selectQuery(
        filters = f,
        limit = {'start': request.args.get('start'), 'length': request.args.get('length')},
        order = o
    )
    rows = execute_db(query, values)

    j = jsonify(
        draw = int(request.args.get('draw')),
        recordsTotal = recordsTotal,
        recordsFiltered = recordsFiltered,
        data = rows
    )

    return j
