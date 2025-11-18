import sqlite3
import threading
import time

DB_FILE = "events.db"
# CRITICAL: Lock for thread-safe database access
db_lock = threading.Lock()

def get_db_connection():
    """Returns a new database connection with row factory enabled."""
    # check_same_thread=False is needed when connecting from multiple threads
    # (like the sensor_loop and the Flask request handlers)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
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
                                                            # IMPROVEMENT: Use REAL for numeric timestamp
                                                            timestamp REAL
                      )
                      ''')
            conn.commit()
            print("[INFO] Database initialized successfully.")
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
            # Use a numeric timestamp for better sorting and queries
            timestamp = time.time()

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