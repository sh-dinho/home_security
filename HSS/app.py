from flask import Flask, render_template, Response
from motion import MotionDetector

app = Flask(__name__)

# Initialize motion detector with simulated video
motion_detector = MotionDetector("static/placeholder.jpg")

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    import cv2
    app.run(host='0.0.0.0', port=5000, debug=True)
