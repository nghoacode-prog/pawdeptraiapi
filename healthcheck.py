import sys
from core import *
init_db();seed();bad=[x['code'] for x in rows('SELECT * FROM tables_ WHERE is_active=1 AND last_poll_at IS NULL')]
print({'ok':not bad,'tables':len(rows('SELECT code FROM tables_')),'never_polled':bad});sys.exit(1 if bad else 0)
