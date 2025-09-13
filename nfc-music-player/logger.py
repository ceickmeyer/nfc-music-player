import datetime
import os

class ActivityLogger:
    def __init__(self, log_file="logs/activity.log"):
        self.log_file = log_file
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Log startup
        self.log_activity("SYSTEM", "Music Player", "started")
    
    def log_activity(self, nfc_id, album, action):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | NFC: {nfc_id} | Album: {album} | Action: {action}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠️  Logging error: {e}")
        
        # Also print to console (except system messages)
        if nfc_id != "SYSTEM":
            print(f"📝 {timestamp} | {album} | {action}")
    
    def get_recent_activity(self, lines=10):
        """Get recent activity from log file"""
        try:
            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) >= lines else all_lines
        except Exception as e:
            print(f"Could not read log file: {e}")
            return []
