# database.py
import sqlite3
from datetime import datetime

DB_FILE = "events.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS events (
                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                    event_type TEXT,
                                                    description TEXT,
                                                    timestamp TEXT
              )
              ''')
    conn.commit()
    conn.close()

def log_event(event_type, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
              INSERT INTO events (event_type, description, timestamp)
              VALUES (?, ?, ?)
              ''', (event_type, description, timestamp))
    conn.commit()
    conn.close()
