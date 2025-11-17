import cv2
import numpy as np
import time

class MotionDetector:
    def __init__(self, video_source):
        """
        video_source: path to a video file or image for simulation
        """
        # If image, we simulate a video by repeating it
        self.is_image = video_source.lower().endswith(('.jpg', '.png'))
        if self.is_image:
            self.frame = cv2.imread(video_source)
        else:
            self.cap = cv2.VideoCapture(video_source)

        self.prev_frame = None

    def detect_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            return frame

        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 500:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        self.prev_frame = gray
        return frame

    def get_frames(self):
        while True:
            if self.is_image:
                frame = self.frame.copy()
                frame = self.detect_motion(frame)
                yield frame
                time.sleep(0.1)
            else:
                ret, frame = self.cap.read()
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                frame = self.detect_motion(frame)
                yield frame
