import json
import time
from config import TELEMETRY_FILE

def log_event(event_type, data):
    entry = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "event": event_type,
        **data
    }
    
    print(f"[TELEMETRY] Logging event: {event_type}")
    
    with open(TELEMETRY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    print(f"[TELEMETRY] Written to {TELEMETRY_FILE}")