# motion_ai.py
import cv2
import numpy as np
import os
from alerts import send_alert
import time
import random

class AIMotionDetector:
    def __init__(self, video_source="static/placeholder.jpg"):
        self.is_image = video_source.lower().endswith(('.jpg', '.png'))
        if self.is_image:
            self.frame = cv2.imread(video_source)
            if self.frame is None:
                raise FileNotFoundError(f"Could not load image: {video_source}")
        else:
            self.cap = cv2.VideoCapture(video_source)

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
        if self.ai_enabled:
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                         (300, 300), (104.0, 177.0, 123.0))
            self.net.setInput(blob)
            detections = self.net.forward()

            human_detected = False
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.5:
                    human_detected = True
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
            return human_detected, frame
        else:
            # Simulated motion: randomly trigger detection 10% of the time
            human_detected = random.random() < 0.1
            if human_detected:
                send_alert("Simulated human detected!", event_type="Motion")
            return human_detected, frame

    def get_frames(self):
        while True:
            if self.is_image:
                frame = self.frame.copy()
                detected, frame = self.detect_human(frame)
                yield frame
                time.sleep(0.1)
            else:
                ret, frame = self.cap.read()
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                detected, frame = self.detect_human(frame)
                yield frame
