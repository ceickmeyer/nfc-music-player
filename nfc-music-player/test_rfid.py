#!/usr/bin/env python3
"""
RFID Reader Hardware Test
Place this file in $HOME/nfc-music-player/test_rfid.py
Run with: python3 test_rfid.py
"""

import time
import sys

try:
    from mfrc522 import SimpleMFRC522
    import RPi.GPIO as GPIO
    print("✓ All required libraries imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Run the setup script first to install dependencies!")
    sys.exit(1)

def test_rfid_reader():
    print("\n=== RFID Reader Hardware Test ===")
    print("Make sure your RC522 is wired correctly:")
    print("SDA/SS  -> Pin 24 (GPIO8)")
    print("SCK     -> Pin 23 (GPIO11)")
    print("MOSI    -> Pin 19 (GPIO10)")
    print("MISO    -> Pin 21 (GPIO9)")
    print("IRQ     -> Not connected")
    print("GND     -> Pin 6 (Ground)")
    print("RST     -> Pin 22 (GPIO25)")
    print("3.3V    -> Pin 1 (3.3V)")
    print()
    
    reader = SimpleMFRC522()
    
    print("Testing RFID reader...")
    print("Place an NFC tag/card on the reader within 10 seconds...")
    
    start_time = time.time()
    tag_detected = False
    
    while time.time() - start_time < 10:  # 10 second timeout
        try:
            id, text = reader.read_no_block()
            if id:
                print(f"✓ SUCCESS: Tag detected!")
                print(f"  Tag ID: {id}")
                print(f"  Tag Text: '{text.strip()}'")
                tag_detected = True
                break
        except Exception as e:
            print(f"✗ Error reading tag: {e}")
            break
        
        time.sleep(0.5)
    
    if not tag_detected:
        print("✗ No tag detected within 10 seconds")
        print("\nTroubleshooting:")
        print("1. Check all wiring connections")
        print("2. Ensure SPI is enabled: sudo raspi-config -> Interface Options -> SPI")
        print("3. Try a different NFC tag/card")
        print("4. Verify 3.3V power supply to the RC522")
    
    print("\nContinuous reading test (Ctrl+C to stop)...")
    print("Place and remove tags to test detection...")
    
    try:
        last_id = None
        while True:
            id, text = reader.read_no_block()
            
            if id and id != last_id:
                print(f"Tag placed: {id}")
                last_id = id
            elif not id and last_id:
                print(f"Tag removed: {last_id}")
                last_id = None
            
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        print("\nTest completed!")
    
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    test_rfid_reader()
