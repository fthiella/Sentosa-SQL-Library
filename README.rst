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