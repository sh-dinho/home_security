# motion.py
import cv2
import numpy as np
import os
from alerts import send_alert
import time
import random

class AIMotionDetector:
    def __init__(self, video_source="static/placeholder.jpg", get_armed_state=None):
        self.is_image = video_source.lower().endswith(('.jpg', '.png'))
        if self.is_image:
            self.frame = cv2.imread(video_source)
            if self.frame is None:
                raise FileNotFoundError(f"Could not load image: {video_source}")
        else:
            self.cap = cv2.VideoCapture(video_source)

        # Function to check the global armed state from app.py
        self.get_armed_state = get_armed_state

        # Try loading AI model
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        prototxt_path = os.path.join(BASE_DIR, "deploy.prototxt.txt")
        caffemodel_path = os.path.join(BASE_DIR, "res10_300x300_ssd_iter_140000.caffemodel")

        if os.path.exists(prototxt_path) and os.path.exists(caffemodel_path):
            self.ai_enabled = True
            self.net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)
            print("[INFO] AI human detection enabled")
        else:
            self.ai_enabled = False
            print("[INFO] AI model not found, using simulated motion detection")

    def detect_human(self, frame):
        # Check the system's armed status
        is_armed = self.get_armed_state() if self.get_armed_state else False

        human_detected = False

        if self.ai_enabled:
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                         (300, 300), (104.0, 177.0, 123.0))
            self.net.setInput(blob)
            detections = self.net.forward()

            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.5:
                    human_detected = True
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    # Draw a red or gray box depending on armed status
                    color = (0, 0, 255) if is_armed else (100, 100, 100)
                    cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

            if human_detected and is_armed:
                send_alert("AI Human Detected!", event_type="Motion")

        else:
            # Simulated motion
            if random.random() < 0.1:
                human_detected = True
                if is_armed:
                    send_alert("Simulated human detected!", event_type="Motion")
                else:
                    print("[DISARMED] Simulated human detected.")

        return human_detected, frame

    def get_frames(self):
        while True:
            if self.is_image:
                frame = self.frame.copy()
                detected, frame = self.detect_human(frame)
                yield frame
                time.sleep(0.1)
            else:
                if not self.cap or not self.cap.isOpened():
                    print("Video source error. Re-initializing...")
                    self.cap = cv2.VideoCapture(0) # Fallback to webcam
                    time.sleep(2)
                    continue

                ret, frame = self.cap.read()
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                detected, frame = self.detect_human(frame)
                yield frame