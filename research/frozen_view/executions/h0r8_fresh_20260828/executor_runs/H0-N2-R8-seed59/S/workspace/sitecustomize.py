# Installed by frozen_view.run; ordinary sqlite3 API, audit only.
import json, os, re, sqlite3, threading, time
from pathlib import Path
_audit = Path(os.environ.get("FROZEN_VIEW_SQL_AUDIT", "sql_queries.jsonl"))
_lock = threading.Lock()
_real_connect = sqlite3.connect

def _ids(value):
    if isinstance(value, str): return [value] if ":" in value else []
    if isinstance(value, (list, tuple)): return sum((_ids(x) for x in value), [])
    return []
def _emit(event):
    event["order"] = time.time_ns()
    with _lock:
        with _audit.open("a", encoding="utf-8") as h: h.write(json.dumps(event, default=str) + "\n")
class AuditCursor(sqlite3.Cursor):
    def execute(self, sql, parameters=()):
        _emit({"event": "sql_query", "query_text": str(sql), "parameters": repr(parameters)})
        return super().execute(sql, parameters)
    def executemany(self, sql, parameters):
        _emit({"event": "sql_query_many", "query_text": str(sql)})
        return super().executemany(sql, parameters)
    def executescript(self, script):
        _emit({"event": "sql_script", "query_text": str(script)})
        return super().executescript(script)
    def fetchone(self):
        value = super().fetchone(); _emit({"event": "sql_result", "returned_ids": _ids(value)}); return value
    def fetchall(self):
        value = super().fetchall(); _emit({"event": "sql_result", "returned_ids": _ids(value)}); return value
class AuditConnection(sqlite3.Connection):
    def cursor(self, factory=AuditCursor): return super().cursor(factory)
    def execute(self, sql, parameters=()): return self.cursor().execute(sql, parameters)
    def executemany(self, sql, parameters): return self.cursor().executemany(sql, parameters)
    def executescript(self, script): return self.cursor().executescript(script)
def connect(database, *args, **kwargs):
    if Path(str(database)).name == "view.sqlite" and "factory" not in kwargs:
        kwargs["factory"] = AuditConnection
    return _real_connect(database, *args, **kwargs)
sqlite3.connect = connect
