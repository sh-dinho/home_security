# sensors.py
import random
import time
from alerts import send_alert

class SimulatedSensor:
    def __init__(self, name):
        self.name = name
        self.state = "closed"

    def trigger(self, is_armed):
        """
        Triggers the sensor simulation.
        An alert is only sent if the system is ARMED.
        """
        if random.random() < 0.05:  # 5% chance to toggle
            self.state = "open" if self.state == "closed" else "closed"

            if self.state == "open":
                message = f"{self.name} sensor triggered! Door/Window opened."
                if is_armed:
                    # Only send a high-priority alert if the system is armed
                    send_alert(message, event_type="Sensor")
                else:
                    # Otherwise, just print to console for debugging
                    print(f"[DISARMED] {message}")
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

    def check_sensors(self, is_armed):
        """
        Checks all sensors, passing the current armed state to each.
        """
        states = {}
        for sensor in self.sensors:
            states[sensor.name] = sensor.trigger(is_armed)
        return states