# This is a placeholder for real sensor input
# Replace with RPi.GPIO or gpiozero code when hardware is connected

class SensorSimulator:
    def __init__(self):
        self.motion = False
        self.door_open = False

    def read_sensors(self):
        # Example: randomly trigger motion
        import random
        self.motion = random.choice([True, False])
        self.door_open = random.choice([True, False])
        return {"motion": self.motion, "door_open": self.door_open}
