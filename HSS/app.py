# app.py
from flask import Flask, render_template, Response
from motion import AIMotionDetector
from sensors import SensorManager
from database import init_db
import cv2
import threading
import time
import sqlite3

app = Flask(__name__)

# Initialize database
init_db()

# Initialize modules
motion_detector = AIMotionDetector("static/placeholder.jpg")
sensor_manager = SensorManager()
sensor_states = {}

# Background thread for sensors
def sensor_loop():
    global sensor_states
    while True:
        sensor_states = sensor_manager.check_sensors()
        time.sleep(1)

threading.Thread(target=sensor_loop, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html', sensor_states=sensor_states)

def gen_frames():
    for frame in motion_detector.get_frames():
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/events')
def events():
    conn = sqlite3.connect("events.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, event_type, description FROM events ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return render_template("events.html", events=rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
