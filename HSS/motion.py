# motion.py
import cv2
import numpy as np
import os
from alerts import send_alert
import time
import random

# Configuration for frame rate limiting (10 FPS maximum)
MAX_FPS = 10
FRAME_DELAY = 1 / MAX_FPS

class AIMotionDetector:
    def __init__(self, video_source="static/placeholder.jpg", get_armed_state=None):
        self.is_image = video_source.lower().endswith(('.jpg', '.png'))
        if self.is_image:
            self.frame = cv2.imread(video_source)
            if self.frame is None:
                # Handle missing placeholder image gracefully
                print(f"WARNING: Could not load image: {video_source}. Disabling image mode.")
                self.is_image = False
                self.cap = cv2.VideoCapture(0) # Fallback to webcam

        else:
            self.cap = cv2.VideoCapture(video_source)

        # Function to check the global armed state from app.py
        self.get_armed_state = get_armed_state

        # Try loading AI model
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # IMPROVEMENT: Use the correct file names for the model files
        prototxt_path = os.path.join(BASE_DIR, "deploy.prototxt")
        caffemodel_path = os.path.join(BASE_DIR, "res10_300x300_ssd_iter_140000.caffemodel")

        if os.path.exists(prototxt_path) and os.path.exists(caffemodel_path):
            self.ai_enabled = True
            try:
                # Attempt to load the model
                self.net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)
                print("[INFO] AI human detection enabled")
            except Exception as e:
                self.ai_enabled = False
                print(f"[ERROR] Failed to load AI model: {e}. Falling back to simulation.")
        else:
            self.ai_enabled = False
            print("[INFO] AI model files not found. Falling back to simulation.")


    def _detect_ai(self, frame):
        """Performs actual AI detection using the loaded model."""
        (h, w) = frame.shape[:2]
        # Resize frame to 300x300, normalize, and create blob
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))

        self.net.setInput(blob)
        detections = self.net.forward()
        human_detected = False
        is_armed = self.get_armed_state()

        # Iterate over detections
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            # Filter out weak detections by ensuring the confidence is greater than the minimum confidence
            if confidence > 0.5:
                # We'll use this model for general human/face detection in this context (assuming 'person' or 'face' index 1 or 15)
                # Note: The provided model (res10_300x300_ssd) is for Face Detection (class index 1 is face).
                # We'll treat a detected face as a person for this security system.

                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # Draw a red or gray box depending on armed status
                color = (0, 0, 255) if is_armed else (100, 100, 100)
                cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

                human_detected = True

        return human_detected, frame

    def _detect_simulated(self, frame):
        """Simulates human detection for systems without the AI model."""
        human_detected = False
        is_armed = self.get_armed_state()

        # 10% chance to simulate detection
        if random.random() < 0.1:
            human_detected = True
            if is_armed:
                send_alert("Simulated human detected! (AI Model Unavailable)", event_type="Motion")
            else:
                print("[DISARMED] Simulated human detected.")

        return human_detected, frame

    def detect_human(self, frame):
        """Delegates detection to AI or simulation based on availability."""
        if self.ai_enabled:
            return self._detect_ai(frame)
        else:
            return self._detect_simulated(frame)

    def get_frames(self):
        """Generator that yields frames for the video feed."""
        while True:
            # PERFORMANCE IMPROVEMENT: Frame Rate Limiter
            start_time = time.time()

            if self.is_image:
                frame = self.frame.copy()
                detected, frame = self.detect_human(frame)
                yield frame
                time.sleep(1) # Slow down image processing
            else:
                # Video capture loop
                if not self.cap or not self.cap.isOpened():
                    print("Video source error. Re-initializing...")
                    self.cap = cv2.VideoCapture(0) # Fallback to webcam
                    time.sleep(2)
                    continue

                ret, frame = self.cap.read()
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Restart video stream if it ends
                    continue

                detected, frame = self.detect_human(frame)
                yield frame

            # Frame rate limiting logic
            elapsed_time = time.time() - start_time
            if elapsed_time < FRAME_DELAY:
                time.sleep(FRAME_DELAY - elapsed_time)