# -*- coding: utf-8 -*-
"""
Python Backend "Sentosa SQL Library" for DataTables and Frontend applications
"""
import re

# parse Datatable Args

def __int_str(v):
    if v.isdigit():
        return(int(v))
    return v

def parseDatatableArgs(args):
    p = {}
    for a in args:
        if a in ['draw', 'start', 'length', '_']:
            p[a] = args.get(a)
        else:
            m = re.match(
                r'^(\w+)(?:\[(\w+)\])(?:\[(\w+)\])?(?:\[(\w+)\])?$',
                a
            )
            if m:
                g = m.groups()

                if g[0] not in p:
                    p[__int_str(g[0])] = {}

                if g[1] is None:
                    p[__int_str(g[0])] = args.get(a)
                    continue

                if g[1] is not None and __int_str(g[1]) not in p[__int_str(g[0])]:
                    p[__int_str(g[0])][__int_str(g[1])] = {}

                if g[2] is None:
                    p[__int_str(g[0])][__int_str(g[1])] = args.get(a)
                    continue

                if g[2] is not None and __int_str(g[2]) not in p[__int_str(g[0])][__int_str(g[1])]:
                    p[__int_str(g[0])][__int_str(g[1])][__int_str(g[2])] = {}

                if g[3] is None:
                    p[__int_str(g[0])][__int_str(g[1])][__int_str(g[2])] = args.get(a)
                    continue

                p[__int_str(g[0])][__int_str(g[1])][__int_str(g[2])][__int_str(g[3])] = args.get(a)
            else:
                print("{} not matched".format(a))

    return p
