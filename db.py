import sqlite3
from flask import g

DATABASE = "database.db"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def execute(sql, params=()):
    db = get_db()
    db.execute(sql, params)
    db.commit()

def query(sql, params=()):
    db = get_db()
    return db.execute(sql, params).fetchall()
