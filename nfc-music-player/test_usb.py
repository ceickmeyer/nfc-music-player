#!/usr/bin/env python3
"""
USB Drive Music Detection Test
Place this file in $HOME/nfc-music-player/test_usb.py
Run with: python3 test_usb.py
"""

import os
import glob
from mutagen.mp3 import MP3
import subprocess

def find_usb_drives():
    """Find all mounted USB drives"""
    usb_paths = []
    media_dir = "/media/pi/"
    
    if os.path.exists(media_dir):
        for item in os.listdir(media_dir):
            path = os.path.join(media_dir, item)
            if os.path.ismount(path):
                usb_paths.append(path)
    
    # Also check /mnt for manually mounted drives
    mnt_dir = "/mnt/"
    if os.path.exists(mnt_dir):
        for item in os.listdir(mnt_dir):
            path = os.path.join(mnt_dir, item)
            if os.path.ismount(path) and path not in usb_paths:
                usb_paths.append(path)
    
    return usb_paths

def analyze_music_structure(base_path):
    """Analyze the music folder structure"""
    print(f"\nAnalyzing music structure in: {base_path}")
    print("=" * 50)
    
    if not os.path.exists(base_path):
        print(f"✗ Path does not exist: {base_path}")
        return {}
    
    albums = {}
    total_mp3s = 0
    
    # Look for folders (albums)
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        
        if os.path.isdir(item_path):
            # Find MP3 files in this folder
            mp3_files = glob.glob(os.path.join(item_path, "*.mp3"))
            
            if mp3_files:
                albums[item] = {
                    'path': item_path,
                    'files': mp3_files,
                    'count': len(mp3_files)
                }
                total_mp3s += len(mp3_files)
                
                print(f"📁 Album: {item}")
                print(f"   Files: {len(mp3_files)} MP3s")
                
                # Show first few songs
                for i, mp3_file in enumerate(sorted(mp3_files)[:3]):
                    filename = os.path.basename(mp3_file)
                    
                    # Try to get song duration
                    try:
                        audio = MP3(mp3_file)
                        duration = int(audio.info.length)
                        duration_str = f"{duration//60}:{duration%60:02d}"
                    except:
                        duration_str = "?:??"
                    
                    print(f"   ♪ {filename} [{duration_str}]")
                
                if len(mp3_files) > 3:
                    print(f"   ... and {len(mp3_files) - 3} more files")
                print()
    
    print(f"Summary: {len(albums)} albums, {total_mp3s} total MP3 files")
    return albums

def test_audio_output():
    """Test audio output configuration"""
    print("\n=== Audio Output Test ===")
    
    try:
        # Check available audio devices
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        print("Available audio devices:")
        print(result.stdout)
        
        # Check current audio output
        result = subprocess.run(['amixer', 'cget', 'numid=3'], capture_output=True, text=True)
        if 'values=1' in result.stdout:
            print("✓ Audio output: 3.5mm jack")
        elif 'values=2' in result.stdout:
            print("✓ Audio output: HDMI")
        else:
            print("? Audio output: Unknown")
            
        print("\nTo change audio output:")
        print("  3.5mm jack: sudo amixer cset numid=3 1")
        print("  HDMI:       sudo amixer cset numid=3 2")
            
    except Exception as e:
        print(f"Could not check audio configuration: {e}")

def main():
    print("=== USB Drive Music Detection Test ===")
    
    # Find USB drives
    usb_drives = find_usb_drives()
    
    if not usb_drives:
        print("✗ No USB drives found!")
        print("\nTroubleshooting:")
        print("1. Make sure USB drive is plugged in")
        print("2. Check if it's mounted: lsblk")
        print("3. Try manually mounting: sudo mount /dev/sda1 /mnt/usb")
        return
    
    print(f"✓ Found {len(usb_drives)} mounted USB drive(s):")
    for drive in usb_drives:
        print(f"  - {drive}")
    
    # Analyze each drive
    all_albums = {}
    
    for drive_path in usb_drives:
        albums = analyze_music_structure(drive_path)
        if albums:
            all_albums[drive_path] = albums
        
        # Also check for MUSIC subfolder
        music_path = os.path.join(drive_path, "MUSIC")
        if os.path.exists(music_path):
            print(f"\nFound MUSIC subfolder: {music_path}")
            albums = analyze_music_structure(music_path)
            if albums:
                all_albums[music_path] = albums
    
    if not all_albums:
        print("\n✗ No music albums found on any USB drive!")
        print("\nExpected structure:")
        print("USB_Drive/")
        print("├── Album1/")
        print("│   ├── 01-song1.mp3")
        print("│   └── 02-song2.mp3")
        print("└── Album2/")
        print("    ├── track01.mp3")
        print("    └── track02.mp3")
    else:
        print(f"\n✓ Music collection detected successfully!")
        
        # Suggest best path for config
        best_path = max(all_albums.keys(), key=lambda x: len(all_albums[x]))
        print(f"\nRecommended USB path for config.json: {best_path}")
    
    # Test audio output
    test_audio_output()

if __name__ == "__main__":
    main()
