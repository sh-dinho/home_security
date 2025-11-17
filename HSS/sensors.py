# sensors.py
import random
import time
from alerts import send_alert

class SimulatedSensor:
    def __init__(self, name):
        self.name = name
        self.state = "closed"

    def trigger(self):
        if random.random() < 0.05:  # 5% chance to toggle
            self.state = "open" if self.state == "closed" else "closed"
            if self.state == "open":
                send_alert(f"{self.name} sensor triggered! Door/Window opened.", event_type="Sensor")
            else:
                print(f"{self.name} sensor reset to closed.")
        return self.state

class SensorManager:
    def __init__(self):
        self.sensors = [
            SimulatedSensor("Front Door"),
            SimulatedSensor("Back Door"),
            SimulatedSensor("Living Room Window")
        ]

    def check_sensors(self):
        states = {}
        for sensor in self.sensors:
            states[sensor.name] = sensor.trigger()
        return states
