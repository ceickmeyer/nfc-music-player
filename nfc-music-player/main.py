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
    
    def get_album_info(self, nfc_id):
        """Get album name and shuffle preference from config"""
        mapping = self.config['nfc_mappings'].get(nfc_id)
        
        if not mapping:
            return None, False
        
        # Support both old format (string) and new format (dict)
        if isinstance(mapping, str):
            return mapping, False  # Old format, no shuffle
        else:
            return mapping.get('album'), mapping.get('shuffle', False)
    
    def run(self):
        print("NFC Music Player started...")
        print(f"Monitoring for NFC tags...")
        
        # Check if USB drive is available
        if not os.path.exists(self.config['usb_mount_path']):
            print(f"⚠️  USB drive not found at: {self.config['usb_mount_path']}")
            print("Waiting for USB drive to be connected...")
        else:
            print(f"✅ Music path: {self.config['usb_mount_path']}")
            
            # Display available albums with shuffle info
            albums = []
            for nfc_id, mapping in self.config['nfc_mappings'].items():
                if isinstance(mapping, str):
                    albums.append(f"{mapping}")
                else:
                    album = mapping.get('album', 'Unknown')
                    shuffle_text = " (shuffled)" if mapping.get('shuffle', False) else ""
                    albums.append(f"{album}{shuffle_text}")
            
            print(f"✅ Available albums: {albums}")
        
        print("Press Ctrl+C to stop\n")
        
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
            print("\nShutting down...")
            self.music_player.stop()
            self.nfc_reader.cleanup()
    
    def handle_new_tag(self, nfc_id):
        album, shuffle = self.get_album_info(nfc_id)
        
        if album:
            shuffle_text = " (shuffled)" if shuffle else ""
            print(f"🎵 Tag detected! Playing album: {album}{shuffle_text}")
            
            if self.music_player.play_album(album, shuffle=shuffle):
                self.current_nfc_id = nfc_id
                self.is_playing = True
                action = "started_shuffled" if shuffle else "started"
                self.logger.log_activity(nfc_id, album, action)
            else:
                print(f"❌ Album '{album}' not found or no MP3 files")
        else:
            print(f"❓ Unknown NFC ID: {nfc_id}")
            print("Add this ID to config.json to map it to an album")
            self.logger.log_activity(nfc_id, "Unknown", "unknown_tag")
    
    def handle_tag_removed(self):
        album, shuffle = self.get_album_info(self.current_nfc_id)
        if not album:
            album = "Unknown"
        
        shuffle_text = " (shuffled)" if shuffle else ""
        print(f"🛑 Tag removed - stopping playback of: {album}{shuffle_text}")
        self.music_player.stop()
        
        action = "stopped_shuffled" if shuffle else "stopped"
        self.logger.log_activity(self.current_nfc_id, album, action)
        self.current_nfc_id = None
        self.is_playing = False

if __name__ == "__main__":
    controller = NFCMusicController()
    controller.run()