from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

class NFCReader:
    def __init__(self):
        self.reader = SimpleMFRC522()
        # Suppress GPIO warnings if already in use
        GPIO.setwarnings(False)
    
    def read_tag(self):
        try:
            id, text = self.reader.read_no_block()
            return str(id) if id else None
        except Exception as e:
            # Suppress AUTH errors since they're normal for our tags
            if "AUTH ERROR" not in str(e):
                print(f"NFC read error: {e}")
            return None
    
    def cleanup(self):
        try:
            GPIO.cleanup()
        except:
            pass  # Ignore cleanup errors
