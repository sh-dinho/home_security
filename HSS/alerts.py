# alerts.py
from database import log_event

def send_alert(message, event_type="ALERT"):
    """
    Alert system that logs the event.
    """
    print(f"[{event_type}] {message}")
    log_event(event_type, message)
