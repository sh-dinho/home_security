# motion_ai.py
import cv2
import numpy as np
from alerts import send_alert
import time

class AIMotionDetector:
    def __init__(self, video_source="static/placeholder.jpg"):
        self.is_image = video_source.lower().endswith(('.jpg', '.png'))
        if self.is_image:
            self.frame = cv2.imread(video_source)
        else:
            self.cap = cv2.VideoCapture(video_source)

        # Pre-trained OpenCV DNN for face/human detection
        self.net = cv2.dnn.readNetFromCaffe(
            "deploy.prototxt.txt",
            "res10_300x300_ssd_iter_140000.caffemodel"
        )

    def detect_human(self, frame):
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

    def get_frames(self):
        while True:
            if self.is_image:
                frame = self.frame.copy()
                detected, frame = self.detect_human(frame)
                if detected:
                    send_alert("Human detected!", event_type="Motion")
                yield frame
                time.sleep(0.1)
            else:
                ret, frame = self.cap.read()
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                detected, frame = self.detect_human(frame)
                if detected:
                    send_alert("Human detected!", event_type="Motion")
                yield frame
