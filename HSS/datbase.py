import sqlite3

DB_FILE = "events.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, event TEXT)''')
    conn.commit()
    conn.close()

def log_event(event):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO events (event) VALUES (?)", (event,))
    conn.commit()
    conn.close()
