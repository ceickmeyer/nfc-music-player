# NFC Music Player - Raspberry Pi Project

## Project Overview
Build an NFC-controlled music player using a Raspberry Pi 3 and RC522 RFID reader. When an NFC sticker is placed on the reader, it plays the associated album/playlist through the 3.5mm audio jack. Removing the sticker stops playback.

## Hardware Requirements
- Raspberry Pi 3
- RC522 RFID/NFC Reader (already wired)
- NFC stickers/tags
- USB drive containing MP3 albums
- 3.5mm audio output (speakers/headphones)

## Software Requirements
```bash
# Install required Python libraries
sudo pip3 install mfrc522 pygame mutagen
```

## Project Structure
```
/home/pi/nfc-music-player/
├── main.py                 # Main application
├── config.json            # NFC ID to album mappings
├── music_player.py         # Audio playback handler
├── nfc_reader.py          # NFC reading functionality
├── logger.py              # Activity logging
└── logs/
    └── activity.log       # Play history
```

## File Organization
- USB drive mounted at `/media/pi/MUSIC/` (or similar)
- Each folder = one album
- Only MP3 files in top-level folders
- Example structure:
```
/media/pi/MUSIC/
├── Album1/
│   ├── 01-song1.mp3
│   └── 02-song2.mp3
└── Album2/
    ├── track01.mp3
    └── track02.mp3
```

## Configuration File (config.json)
```json
{
    "usb_mount_path": "/media/pi/MUSIC",
    "nfc_mappings": {
        "123456789": "Album1",
        "987654321": "Album2"
    },
    "audio_settings": {
        "volume": 0.7
    }
}
```

## Core Implementation Files

### 1. main.py
```python
#!/usr/bin/env python3
import time
import json
import os
from nfc_reader import NFCReader
from music_player import MusicPlayer
from logger import ActivityLogger

class NFCMusicController:
    def __init__(self):
        self.load_config()
        self.nfc_reader = NFCReader()
        self.music_player = MusicPlayer(self.config)
        self.logger = ActivityLogger()
        self.current_nfc_id = None
        self.is_playing = False
        
    def load_config(self):
        with open('config.json', 'r') as f:
            self.config = json.load(f)
    
    def run(self):
        print("NFC Music Player started...")
        try:
            while True:
                nfc_id = self.nfc_reader.read_tag()
                
                if nfc_id and nfc_id != self.current_nfc_id:
                    # New tag detected
                    self.handle_new_tag(nfc_id)
                elif not nfc_id and self.current_nfc_id:
                    # Tag removed
                    self.handle_tag_removed()
                
                time.sleep(0.5)  # Check every 500ms
                
        except KeyboardInterrupt:
            print("Shutting down...")
            self.music_player.stop()
    
    def handle_new_tag(self, nfc_id):
        album = self.config['nfc_mappings'].get(nfc_id)
        
        if album:
            print(f"Playing album: {album}")
            if self.music_player.play_album(album):
                self.current_nfc_id = nfc_id
                self.is_playing = True
                self.logger.log_activity(nfc_id, album, "started")
            else:
                print(f"Album '{album}' not found")
        else:
            print(f"Unknown NFC ID: {nfc_id}")
            self.logger.log_activity(nfc_id, "Unknown", "unknown_tag")
    
    def handle_tag_removed(self):
        print("Tag removed - stopping playback")
        self.music_player.stop()
        album = self.config['nfc_mappings'].get(self.current_nfc_id, "Unknown")
        self.logger.log_activity(self.current_nfc_id, album, "stopped")
        self.current_nfc_id = None
        self.is_playing = False

if __name__ == "__main__":
    controller = NFCMusicController()
    controller.run()
```

### 2. nfc_reader.py
```python
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

class NFCReader:
    def __init__(self):
        self.reader = SimpleMFRC522()
    
    def read_tag(self):
        try:
            id, text = self.reader.read_no_block()
            return str(id) if id else None
        except Exception as e:
            print(f"NFC read error: {e}")
            return None
    
    def cleanup(self):
        GPIO.cleanup()
```

### 3. music_player.py
```python
import pygame
import os
import glob
from mutagen.mp3 import MP3
import threading

class MusicPlayer:
    def __init__(self, config):
        pygame.mixer.init()
        self.config = config
        self.current_playlist = []
        self.current_index = 0
        self.is_playing = False
        self.playback_thread = None
        
        # Set volume
        pygame.mixer.music.set_volume(config['audio_settings']['volume'])
    
    def play_album(self, album_name):
        album_path = os.path.join(self.config['usb_mount_path'], album_name)
        
        if not os.path.exists(album_path):
            return False
        
        # Get all MP3 files in the album folder
        mp3_files = glob.glob(os.path.join(album_path, "*.mp3"))
        mp3_files.sort()  # Play in alphabetical order
        
        if not mp3_files:
            print(f"No MP3 files found in {album_path}")
            return False
        
        self.current_playlist = mp3_files
        self.current_index = 0
        self.is_playing = True
        
        # Start playback in separate thread
        self.playback_thread = threading.Thread(target=self._play_loop)
        self.playback_thread.daemon = True
        self.playback_thread.start()
        
        return True
    
    def _play_loop(self):
        while self.is_playing and self.current_playlist:
            try:
                current_song = self.current_playlist[self.current_index]
                print(f"Playing: {os.path.basename(current_song)}")
                
                pygame.mixer.music.load(current_song)
                pygame.mixer.music.play()
                
                # Wait for song to finish
                while pygame.mixer.music.get_busy() and self.is_playing:
                    pygame.time.wait(100)
                
                if self.is_playing:
                    # Move to next song, loop back to start when done
                    self.current_index = (self.current_index + 1) % len(self.current_playlist)
                    
            except Exception as e:
                print(f"Playback error: {e}")
                break
    
    def stop(self):
        self.is_playing = False
        pygame.mixer.music.stop()
        self.current_playlist = []
        self.current_index = 0
```

### 4. logger.py
```python
import datetime
import os

class ActivityLogger:
    def __init__(self, log_file="logs/activity.log"):
        self.log_file = log_file
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    def log_activity(self, nfc_id, album, action):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | NFC: {nfc_id} | Album: {album} | Action: {action}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Logging error: {e}")
        
        print(log_entry.strip())  # Also print to console
```

## Setup Instructions

### 1. Create Project Directory
```bash
mkdir /home/pi/nfc-music-player
cd /home/pi/nfc-music-player
```

### 2. Create Files
Create all the Python files above and the initial config.json file.

### 3. Make Executable
```bash
chmod +x main.py
```

### 4. Auto-Start Setup
Create a systemd service file:

```bash
sudo nano /etc/systemd/system/nfc-music.service
```

Add the following content:
```ini
[Unit]
Description=NFC Music Player
After=multi-user.target

[Service]
Type=idle
User=pi
WorkingDirectory=/home/pi/nfc-music-player
ExecStart=/usr/bin/python3 /home/pi/nfc-music-player/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl enable nfc-music.service
sudo systemctl start nfc-music.service
```

### 5. USB Drive Setup
- Format USB drive as FAT32
- Create folders for each album
- Place MP3 files in respective folders
- Plug into Raspberry Pi

## Adding New NFC Tags

1. Run the system and place a new NFC sticker on the reader
2. Check the console output or log file for the NFC ID
3. Edit `config.json` to add the mapping:
```json
"nfc_mappings": {
    "existing_id": "ExistingAlbum",
    "new_nfc_id": "NewAlbumFolderName"
}
```
4. Restart the service: `sudo systemctl restart nfc-music.service`

## Troubleshooting

- **No audio**: Check `alsamixer` settings and audio output selection
- **USB not mounting**: Check `/media/pi/` for mount point, update config if needed
- **NFC not reading**: Verify RC522 wiring and SPI is enabled
- **Service not starting**: Check logs with `sudo journalctl -u nfc-music.service`

## Log File Format
```
2024-01-15 14:30:25 | NFC: 123456789 | Album: GreatestHits | Action: started
2024-01-15 14:35:12 | NFC: 123456789 | Album: GreatestHits | Action: stopped
```

This system will continuously monitor for NFC tags and provide seamless music playback based on your physical music collection!