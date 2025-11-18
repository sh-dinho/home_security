from database import log_event

# Function to safely retrieve the armed status from the main application's state
def get_armed_status():
    """Tries to access the armed status from the main application's state."""
    try:
        # Import necessary components from the running app module (using new variable names)
        from app import global_system_armed, system_state_lock
        with system_state_lock:
            return global_system_armed
    except ImportError:
        # Fallback if alerts.py is run standalone (e.g., during testing)
        return True

def send_alert(message, event_type="ALERT"):
    """
    Alert system that prints to console and logs the event to the database,
    but only if the system is armed for Motion/Sensor events.
    """
    is_armed = get_armed_status()

    print(f"🚨 ALERT [{event_type}]: {message} (Armed: {is_armed})")

    # Define which event types are conditional on the armed state
    SECURITY_EVENT_TYPES = ["Motion", "Sensor"]

    # Only log security events if the system is Armed
    if event_type in SECURITY_EVENT_TYPES and not is_armed:
        print(f"INFO: Suppressing logging for {event_type} because the system is Disarmed.")
        return

    # Log all other events (like System status changes) regardless of armed state
    log_event(event_type, message)