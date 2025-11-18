import random
import time
import json
import os
from alerts import send_alert

# Define the path to the configuration file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

class SimulatedSensor:
    """Represents a single sensor loaded from configuration."""
    def __init__(self, name, chance_to_open, initial_state="closed", critical=False, open_state="open"):
        self.name = name
        self.chance_to_open = chance_to_open
        self.state = initial_state
        self.critical = critical
        self.open_state = open_state # State name when the sensor is triggered

    def trigger(self, is_armed):
        """
        Triggers the sensor simulation.
        An alert is only sent if the system is ARMED and the sensor is not critical (or always logs for critical).
        """
        # Determine the chance for the state to change
        if random.random() < self.chance_to_open:
            if self.state == self.open_state:
                # If currently open, 95% chance to reset to initial state (to prevent constant alerts)
                if random.random() > 0.95:
                    self.state = self.initial_state
                    print(f"[INFO] {self.name} sensor reset to {self.initial_state}.")
            else:
                # Sensor triggered
                self.state = self.open_state

                message = f"{self.name} sensor triggered! State: {self.state}."

                # Critical sensors (like smoke) should alert regardless of armed state, but only log a high-priority ALERT.
                if self.critical:
                    # Log as a critical, high-priority ALERT event
                    send_alert(message, event_type="CRITICAL ALERT")
                elif is_armed:
                    # Only log regular security events if the system is armed
                    send_alert(message, event_type="Sensor")
                else:
                    print(f"[DISARMED] {message}")

        return self.state

class SensorManager:
    """Manages all simulated sensors, loading their configuration from a JSON file."""
    def __init__(self):
        self.sensors = self._load_sensors_from_config()

    def _load_sensors_from_config(self):
        """Loads sensor definitions from the config.json file."""
        print(f"[INFO] Loading sensor config from {CONFIG_PATH}")
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)

            sensor_list = []
            for s_data in config.get('sensors', []):
                # Ensure all required parameters are present (using safe .get() with defaults)
                sensor = SimulatedSensor(
                    name=s_data.get("name"),
                    chance_to_open=s_data.get("chance_to_open", 0.05),
                    initial_state=s_data.get("initial_state", "closed"),
                    critical=s_data.get("critical", False),
                    open_state=s_data.get("open_state", "open")
                )
                sensor_list.append(sensor)

            print(f"[INFO] Loaded {len(sensor_list)} sensors.")
            return sensor_list

        except FileNotFoundError:
            print(f"[ERROR] config.json not found at {CONFIG_PATH}. Using default sensors.")
            return self._default_sensors()
        except json.JSONDecodeError:
            print("[ERROR] Invalid JSON format in config.json. Using default sensors.")
            return self._default_sensors()

    def _default_sensors(self):
        """Fallback to hardcoded sensors if config loading fails."""
        return [
            SimulatedSensor("Front Door", 0.05),
            SimulatedSensor("Living Room Window", 0.03),
            SimulatedSensor("Smoke Detector", 0.01, initial_state="clear", critical=True, open_state="smoke detected")
        ]

    def check_sensors(self, is_armed):
        """
        Checks all sensors, passing the current armed state to each.
        Returns a dictionary of {sensor_name: state}.
        """
        states = {}
        for sensor in self.sensors:
            states[sensor.name] = sensor.trigger(is_armed)
        return states