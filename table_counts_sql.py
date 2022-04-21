#!/usr/bin/env python

import sys

if len(sys.argv) < 2:
    raise Exception('At least one table name must be given')

sql = ''
for t in sys.argv[1:]:
    if len(sql) > 0:
        sql += ' UNION '
    sql += f"SELECT '{t}' AS table_name, COUNT(*) FROM {t}"
sql += ';'

print(sql)
