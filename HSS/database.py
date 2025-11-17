import sqlite3
from datetime import datetime
import threading

DB_FILE = "events.db"
# CRITICAL: Lock for thread-safe database access
db_lock = threading.Lock()

def get_db_connection():
    """Returns a new database connection with row factory enabled."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=True)
    # Allows accessing columns by name (e.g., row['description'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    with db_lock:
        conn = None
        try:
            conn = get_db_connection()
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
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
        finally:
            if conn:
                conn.close()

def log_event(event_type, description):
    """Logs an event to the database, thread-safe."""
    with db_lock:
        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            c.execute('''
                      INSERT INTO events (event_type, description, timestamp)
                      VALUES (?, ?, ?)
                      ''', (event_type, description, timestamp))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database logging error: {e}")
        finally:
            if conn:
                conn.close()