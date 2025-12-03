import sqlite3

DB_PATH = "LibraryAg.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  #dict-like
    return conn