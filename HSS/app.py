from flask import Flask, render_template, Response, redirect, url_for
from motion import AIMotionDetector
from sensors import SensorManager
from database import init_db, get_db_connection, log_event
import cv2
import threading
import time
import sqlite3
from datetime import datetime # CRITICAL: Imported for timestamp conversion

# --- Configuration ---
SENSOR_CHECK_INTERVAL = 2  # Seconds between sensor checks
VIDEO_SOURCE = "static/placeholder.jpg" # Use a placeholder image path or 0 for webcam

# --- Global State & Thread Locks ---
global_sensor_states = {}
sensor_state_lock = threading.Lock()

# Global Arming State and Lock
is_armed = False # Start DISARMED by default
arm_state_lock = threading.Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_very_secret_key_here'

# Initialize database on startup
init_db()

# --- Helper Functions for State Management and Formatting ---

def get_armed_state():
    """Returns the current state of the security system (True for ARMED)."""
    with arm_state_lock:
        return is_armed

def get_current_time(timestamp=None):
    """
    Helper function to convert the numeric timestamp (REAL) from the DB
    into a human-readable string.
    """
    if timestamp is not None:
        # Use datetime.fromtimestamp to convert the numeric REAL value from the DB
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- Module Initialization ---
try:
    motion_detector = AIMotionDetector(VIDEO_SOURCE, get_armed_state=get_armed_state)
except FileNotFoundError:
    print(f"WARNING: {VIDEO_SOURCE} not found. Falling back to webcam 0.")
    motion_detector = AIMotionDetector(0, get_armed_state=get_armed_state)

sensor_manager = SensorManager()

# --- Background Sensor Thread ---

def sensor_loop():
    """
    Background thread loop that periodically checks sensors and updates global state.
    """
    global global_sensor_states

    print("[INFO] Sensor simulation loop started.")

    while True:
        try:
            current_armed_state = get_armed_state()
            new_states = sensor_manager.check_sensors(current_armed_state)

            with sensor_state_lock:
                global_sensor_states = new_states

            time.sleep(SENSOR_CHECK_INTERVAL)

        except Exception as e:
            print(f"FATAL ERROR in sensor_loop: {e}")
            time.sleep(5)

        # Start the background thread
sensor_thread = threading.Thread(target=sensor_loop)
sensor_thread.daemon = True
sensor_thread.start()
print(f"[INFO] Sensor loop running on thread: {sensor_thread.name}")


# --- Flask Routes ---

@app.route('/')
def index():
    """Serves the main dashboard."""
    with sensor_state_lock:
        current_states = global_sensor_states.copy()

    current_armed_state = get_armed_state()

    is_alert = any(state != 'closed' and state != 'clear' for state in current_states.values())

    return render_template("index.html",
                           sensor_states=current_states,
                           is_armed=current_armed_state,
                           is_alert=is_alert,
                           now=get_current_time)

@app.route('/arm_disarm', methods=['POST'])
def arm_disarm():
    """Toggles the system's armed state."""
    global is_armed

    with arm_state_lock:
        is_armed = not is_armed
        new_state_text = "ARMED" if is_armed else "DISARMED"

        # Log the system status change
        log_event("System", f"System changed to: {new_state_text}")
        print(f"[INFO] System State: {new_state_text}")

    return redirect(url_for('index'))

def gen_frames():
    """Generator function to stream video frames (called by video_feed route)."""
    try:
        for frame in motion_detector.get_frames():
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    except Exception as e:
        print(f"Error in video feed generator: {e}")

@app.route('/video_feed')
def video_feed():
    """The video streaming route."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/events')
def events():
    """Serves the event log page. ***FIXED FOR NUMERIC TIMESTAMPS***"""
    conn = None
    events_list = []
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Fetch, ordering by the numeric timestamp (REAL)
        c.execute("SELECT timestamp, event_type, description FROM events ORDER BY timestamp DESC LIMIT 100")
        rows = c.fetchall()

        # FIX: Process rows to format the numeric timestamp
        events_list = [
            {
                'timestamp': get_current_time(row['timestamp']), # <-- Format the numeric timestamp using the helper
                'event_type': row['event_type'],
                'description': row['description']
            }
            for row in rows
        ]

    except sqlite3.Error as e:
        print(f"Error fetching events: {e}")
        events_list = []
    finally:
        if conn:
            conn.close()

    # Pass the correctly formatted list of dictionaries to the template
    return render_template("events.html", events=events_list)

if __name__ == '__main__':
    # Setting use_reloader=False is important to prevent the background
    # thread from starting twice in development mode.
    app.run(debug=True, threaded=True, use_reloader=False)