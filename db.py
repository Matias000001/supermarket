"""
This module handles database operations for the application.
It provides functions to connect to the database, execute SQL commands,
and query the database.
"""


import sqlite3
from flask import g


def get_connection():
    """Connects to the SQLite database and enables foreign key support."""
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


def execute(sql, params=None):
    """Executes an SQL command with optional parameters and commits the transaction."""
    if params is None:
        params = []
    con = get_connection()
    result = con.execute(sql, params)
    con.commit()
    g.last_insert_id = result.lastrowid
    con.close()


def last_insert_id():
    """Returns the last inserted row ID."""
    return g.last_insert_id


def query(sql, params=None):
    """Executes a SELECT SQL query with optional parameters and returns the result."""
    if params is None:
        params = []
    con = get_connection()
    result = con.execute(sql, params).fetchall()
    con.close()
    return result
