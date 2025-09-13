#!/usr/bin/env python3
"""
NFC Tag Config Generator with Shuffle Support
Place this file in /home/pi/nfc-music-player/generate_config.py
Run with: python3 generate_config.py
"""

import json
import os
import glob
import time
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

class ConfigGenerator:
    def __init__(self):
        self.reader = SimpleMFRC522()
        self.config = {
            "usb_mount_path": "/media/pi/MUSIC",
            "nfc_mappings": {},
            "audio_settings": {
                "volume": 0.7
            }
        }
        self.albums = []
        
    def find_usb_path(self):
        """Find the best USB path with music"""
        current_user = os.getenv('USER', 'pi')
        paths_to_check = [
            f"/media/{current_user}/MUSIC",
            "/mnt/MUSIC"
        ]
        
        # Check /media/{user}/ for mounted drives
        media_dir = f"/media/{current_user}/"
        if os.path.exists(media_dir):
            for item in os.listdir(media_dir):
                path = os.path.join(media_dir, item)
                if os.path.ismount(path):
                    paths_to_check.append(path)
                    # Also check for MUSIC subfolder
                    music_path = os.path.join(path, "MUSIC")
                    if os.path.exists(music_path):
                        paths_to_check.append(music_path)
        
        # Find path with most albums
        best_path = None
        most_albums = 0
        
        for path in paths_to_check:
            if os.path.exists(path):
                album_count = len([item for item in os.listdir(path) 
                                 if os.path.isdir(os.path.join(path, item)) and 
                                 glob.glob(os.path.join(path, item, "*.mp3"))])
                
                if album_count > most_albums:
                    most_albums = album_count
                    best_path = path
        
        return best_path, most_albums
    
    def scan_albums(self, music_path):
        """Scan for available albums"""
        albums = []
        
        if not os.path.exists(music_path):
            return albums
        
        for item in os.listdir(music_path):
            item_path = os.path.join(music_path, item)
            if os.path.isdir(item_path):
                mp3_files = glob.glob(os.path.join(item_path, "*.mp3"))
                if mp3_files:
                    albums.append({
                        'name': item,
                        'path': item_path,
                        'track_count': len(mp3_files)
                    })
        
        return sorted(albums, key=lambda x: x['name'])
    
    def display_albums(self):
        """Display available albums"""
        print(f"\nFound {len(self.albums)} albums:")
        print("=" * 40)
        
        for i, album in enumerate(self.albums, 1):
            print(f"{i:2d}. {album['name']} ({album['track_count']} tracks)")
        
        print()
    
    def read_nfc_tag(self):
        """Read an NFC tag with timeout"""
        print("Place NFC tag on reader (10 second timeout)...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                id, text = self.reader.read_no_block()
                if id:
                    return str(id)
            except:
                pass
            time.sleep(0.2)
        
        return None
    
    def ask_shuffle_preference(self, album_name):
        """Ask if user wants this album to play shuffled"""
        while True:
            choice = input(f"Play '{album_name}' shuffled? [y/N]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no', '']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no (default: no)")
    
    def interactive_mapping(self):
        """Interactive NFC tag mapping"""
        print("\n=== Interactive NFC Mapping ===")
        print("For each album, place the corresponding NFC tag on the reader")
        print("Press Enter to skip an album, or 'q' to quit")
        print()
        
        for album in self.albums:
            print(f"Album: {album['name']} ({album['track_count']} tracks)")
            
            choice = input("Map this album? [y/N/q]: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice != 'y':
                print("Skipped.\n")
                continue
            
            # Read NFC tag
            tag_id = self.read_nfc_tag()
            
            if tag_id:
                if tag_id in self.config['nfc_mappings']:
                    old_mapping = self.config['nfc_mappings'][tag_id]
                    old_album = old_mapping.get('album', old_mapping) if isinstance(old_mapping, dict) else old_mapping
                    print(f"⚠️  Warning: Tag {tag_id} was already mapped to '{old_album}'")
                    overwrite = input("Overwrite? [y/N]: ").strip().lower()
                    if overwrite != 'y':
                        print("Skipped.\n")
                        continue
                
                # Ask about shuffle preference
                shuffle = self.ask_shuffle_preference(album['name'])
                
                self.config['nfc_mappings'][tag_id] = {
                    "album": album['name'],
                    "shuffle": shuffle
                }
                
                shuffle_text = " (shuffled)" if shuffle else ""
                print(f"✓ Mapped NFC ID {tag_id} to '{album['name']}'{shuffle_text}")
            else:
                print("✗ No tag detected, skipped")
            
            print()
    
    def batch_mapping(self):
        """Batch NFC tag reading - read all tags first, then assign"""
        print("\n=== Batch NFC Mapping ===")
        print("We'll read all your NFC tags first, then let you assign them")
        print()
        
        tags = []
        tag_count = input("How many tags do you want to read? [Press Enter for unlimited]: ")
        
        if tag_count.isdigit():
            max_tags = int(tag_count)
        else:
            max_tags = None
        
        print("Place NFC tags one by one (press Ctrl+C when done):")
        
        try:
            while max_tags is None or len(tags) < max_tags:
                tag_id = self.read_nfc_tag()
                
                if tag_id:
                    if tag_id not in [t['id'] for t in tags]:
                        tags.append({'id': tag_id, 'album': None})
                        print(f"✓ Read tag {len(tags)}: {tag_id}")
                    else:
                        print(f"⚠️  Tag {tag_id} already read")
                else:
                    print("✗ No tag detected, try again")
        
        except KeyboardInterrupt:
            print(f"\nStopped. Read {len(tags)} unique tags.")
        
        if not tags:
            print("No tags were read.")
            return
        
        # Now assign tags to albums
        print(f"\nAssigning {len(tags)} tags to albums...")
        self.display_albums()
        
        for i, tag in enumerate(tags, 1):
            print(f"\nTag {i} (ID: {tag['id']})")
            
            while True:
                choice = input(f"Enter album number (1-{len(self.albums)}), or 's' to skip: ").strip()
                
                if choice.lower() == 's':
                    break
                elif choice.isdigit() and 1 <= int(choice) <= len(self.albums):
                    album_idx = int(choice) - 1
                    album_name = self.albums[album_idx]['name']
                    
                    # Check if album already mapped
                    existing_tag = None
                    for existing_id, existing_mapping in self.config['nfc_mappings'].items():
                        existing_album = existing_mapping.get('album', existing_mapping) if isinstance(existing_mapping, dict) else existing_mapping
                        if existing_album == album_name:
                            existing_tag = existing_id
                            break
                    
                    if existing_tag:
                        print(f"⚠️  Album '{album_name}' already mapped to tag {existing_tag}")
                        overwrite = input("Overwrite? [y/N]: ").strip().lower()
                        if overwrite == 'y':
                            # Remove old mapping
                            del self.config['nfc_mappings'][existing_tag]
                        else:
                            continue
                    
                    # Ask about shuffle preference
                    shuffle = self.ask_shuffle_preference(album_name)
                    
                    self.config['nfc_mappings'][tag['id']] = {
                        "album": album_name,
                        "shuffle": shuffle
                    }
                    
                    shuffle_text = " (shuffled)" if shuffle else ""
                    print(f"✓ Mapped tag {tag['id']} to '{album_name}'{shuffle_text}")
                    break
                else:
                    print("Invalid choice, try again")
    
    def save_config(self):
        """Save configuration to file"""
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        print(f"\n✓ Configuration saved to config.json")
        print(f"✓ Mapped {len(self.config['nfc_mappings'])} NFC tags")
        
        if self.config['nfc_mappings']:
            print("\nMappings:")
            for tag_id, mapping in self.config['nfc_mappings'].items():
                album = mapping['album']
                shuffle_text = " (shuffled)" if mapping['shuffle'] else ""
                print(f"  {tag_id} → {album}{shuffle_text}")
    
    def load_existing_config(self):
        """Load existing configuration if available"""
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    existing_config = json.load(f)
                    print(f"✓ Loaded existing config with {len(existing_config.get('nfc_mappings', {}))} mappings")
                    
                    # Merge with defaults
                    self.config.update(existing_config)
                    return True
            except Exception as e:
                print(f"⚠️  Could not load existing config: {e}")
        
        return False
    
    def run(self):
        """Main configuration generator"""
        print("=== NFC Music Player Config Generator ===")
        
        # Load existing config
        self.load_existing_config()
        
        # Find USB path
        usb_path, album_count = self.find_usb_path()
        
        if not usb_path or album_count == 0:
            print("✗ No music albums found on USB drives!")
            print("Make sure your USB drive is connected and contains album folders with MP3 files")
            return
        
        print(f"✓ Found {album_count} albums in: {usb_path}")
        self.config['usb_mount_path'] = usb_path
        
        # Scan albums
        self.albums = self.scan_albums(usb_path)
        self.display_albums()
        
        # Choose mapping method
        while True:
            print("Mapping methods:")
            print("1. Interactive - Map one album at a time")
            print("2. Batch - Read all tags first, then assign")
            print("3. Skip mapping (just save path)")
            
            choice = input("Choose method [1/2/3]: ").strip()
            
            if choice == '1':
                self.interactive_mapping()
                break
            elif choice == '2':
                self.batch_mapping()
                break
            elif choice == '3':
                break
            else:
                print("Invalid choice, try again\n")
        
        # Save configuration
        self.save_config()
        
        # Cleanup GPIO
        GPIO.cleanup()
        
        print("\n=== Setup Complete! ===")
        print("You can now run the main program: python3 main.py")
        print("Or add more mappings later by running this script again")

if __name__ == "__main__":
    try:
        generator = ConfigGenerator()
        generator.run()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        GPIO.cleanup()
    except Exception as e:
        print(f"\nError: {e}")
        GPIO.cleanup()