# Ordinary sqlite3 with audit only; installed in participant workspace.
import json, os, sqlite3, threading, time
from pathlib import Path
audit_path=Path(os.environ.get("AF_SQL_AUDIT","sql.jsonl")); lock=threading.Lock(); real=sqlite3.connect
def ids(value):
    if isinstance(value,str): return [value] if ":" in value else []
    if isinstance(value,(list,tuple)): return sum((ids(v) for v in value), [])
    return []
def log(event):
    event["order"]=time.time_ns()
    with lock:
        with audit_path.open("a",encoding="utf-8") as h: h.write(json.dumps(event,default=str)+"\n")
class C(sqlite3.Cursor):
    def execute(self, sql, parameters=()): log({"event":"sql_statement","query_text":str(sql),"parameters":repr(parameters)}); return super().execute(sql,parameters)
    def executescript(self, sql): log({"event":"sql_statement","query_text":str(sql)}); return super().executescript(sql)
    def fetchall(self): v=super().fetchall(); log({"event":"sql_result","rows_returned":len(v),"returned_ids":ids(v)}); return v
    def fetchone(self): v=super().fetchone(); log({"event":"sql_result","rows_returned":0 if v is None else 1,"returned_ids":ids(v)}); return v
class D(sqlite3.Connection):
    def cursor(self, factory=C): return super().cursor(factory)
    def execute(self,sql,parameters=()): return self.cursor().execute(sql,parameters)
def connect(database,*args,**kwargs):
    if Path(str(database)).name == "view.sqlite" and "factory" not in kwargs: kwargs["factory"]=D
    return real(database,*args,**kwargs)
sqlite3.connect=connect
