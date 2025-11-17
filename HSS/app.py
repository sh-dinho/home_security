from flask import Flask, render_template, Response, redirect, url_for
from motion import AIMotionDetector
from sensors import SensorManager
from database import init_db, get_db_connection
import cv2
import threading
import time
import sqlite3

# --- Global State & Thread Locks ---
global_sensor_states = {}
sensor_state_lock = threading.Lock()

# Global Arming State and Lock
is_armed = False # Start DISARMED by default
arm_state_lock = threading.Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_very_secret_key_here' # For Flask sessions

# Initialize database on startup
init_db()

# Helper to safely read the armed state for modules
def get_armed_state():
    """Returns the current state of the security system (True for ARMED)."""
    with arm_state_lock:
        return is_armed

# Initialize modules - pass the function to get the armed state
try:
    motion_detector = AIMotionDetector("static/placeholder.jpg", get_armed_state=get_armed_state)
except FileNotFoundError:
    print("WARNING: static/placeholder.jpg not found. Falling back to webcam 0.")
    motion_detector = AIMotionDetector(0, get_armed_state=get_armed_state)

sensor_manager = SensorManager()

# Background thread for sensors
def sensor_loop():
    """Periodically checks sensors and updates global state."""
    global global_sensor_states
    while True:
        # Pass the current armed state to the sensor manager
        current_armed_state = get_armed_state()
        new_states = sensor_manager.check_sensors(is_armed=current_armed_state)

        with sensor_state_lock:
            global_sensor_states.update(new_states)
        time.sleep(1) # Check sensors every 1 second

# Start the background thread
threading.Thread(target=sensor_loop, daemon=True).start()

# Helper function for Jinja (used in index.html to display last check time)
def get_current_time():
    """Returns a string of the current time."""
    return time.strftime("%H:%M:%S")

# --- Flask Routes ---

@app.route('/arm_disarm', methods=['POST'])
def arm_disarm():
    """Toggles the global armed status."""
    global is_armed
    with arm_state_lock:
        is_armed = not is_armed
        state = "ARMED" if is_armed else "DISARMED"
    print(f"[{state}] System status changed to {state}.")
    # Redirect back to the homepage
    return redirect(url_for('index'))


@app.route('/')
def index():
    """Serves the main dashboard page."""
    with sensor_state_lock:
        current_states = global_sensor_states.copy()

    current_armed_state = get_armed_state()

    return render_template('index.html',
                           sensor_states=current_states,
                           is_armed=current_armed_state,
                           now=get_current_time) # Pass function to the template

def gen_frames():
    """Generator function to stream video frames."""
    for frame in motion_detector.get_frames():
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """The video streaming route."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/events')
def events():
    """Serves the event log page."""
    conn = None
    try:
        conn = get_db_connection() # Use the Row-Factory connection
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, description FROM events ORDER BY id DESC LIMIT 100")
        rows = c.fetchall() # Returns a list of Row objects (like dicts)
    except sqlite3.Error as e:
        print(f"Error fetching events: {e}")
        rows = []
    finally:
        if conn:
            conn.close()

    return render_template("events.html", events=rows)

if __name__ == '__main__':
    # Setting use_reloader=False is important to prevent the background
    # thread from starting twice in debug mode.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)