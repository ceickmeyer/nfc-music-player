import pygame
import os
import glob
from mutagen.mp3 import MP3
import threading
import random

class MusicPlayer:
    def __init__(self, config):
        # Initialize pygame mixer
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        
        self.config = config
        self.current_playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_shuffled = False
        self.playback_thread = None
        
        # Set volume
        volume = config['audio_settings'].get('volume', 0.7)
        pygame.mixer.music.set_volume(volume)
        print(f"Audio initialized - Volume: {int(volume*100)}%")
    
    def play_album(self, album_name, shuffle=False):
        album_path = os.path.join(self.config['usb_mount_path'], album_name)
        
        if not os.path.exists(album_path):
            print(f"❌ Album path not found: {album_path}")
            return False
        
        # Get all MP3 files in the album folder
        mp3_files = glob.glob(os.path.join(album_path, "*.mp3"))
        mp3_files.sort()  # Start with alphabetical order
        
        if not mp3_files:
            print(f"❌ No MP3 files found in {album_path}")
            return False
        
        # Stop current playback if any
        self.stop()
        
        # Shuffle the playlist if requested
        if shuffle:
            random.shuffle(mp3_files)
            self.is_shuffled = True
        else:
            self.is_shuffled = False
        
        self.current_playlist = mp3_files
        self.current_index = 0
        self.is_playing = True
        
        shuffle_text = " (shuffled)" if shuffle else ""
        print(f"🎵 Starting album: {album_name}{shuffle_text} ({len(mp3_files)} tracks)")
        
        # Start playback in separate thread
        self.playback_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.playback_thread.start()
        
        return True
    
    def _play_loop(self):
        while self.is_playing and self.current_playlist:
            try:
                current_song = self.current_playlist[self.current_index]
                song_name = os.path.basename(current_song)
                
                track_info = f"♪ Now playing: {song_name}"
                if self.is_shuffled:
                    track_info += f" [track {self.current_index + 1}/{len(self.current_playlist)}]"
                print(track_info)
                
                # Load and play the song
                pygame.mixer.music.load(current_song)
                pygame.mixer.music.play()
                
                # Wait for song to finish or be stopped
                while pygame.mixer.music.get_busy() and self.is_playing:
                    pygame.time.wait(100)
                
                if self.is_playing:
                    # Move to next song, loop back to start when album ends
                    self.current_index = (self.current_index + 1) % len(self.current_playlist)
                    
                    # Add small pause between tracks
                    if self.is_playing:
                        pygame.time.wait(500)
                    
            except Exception as e:
                print(f"❌ Playback error: {e}")
                # Try next song
                if self.is_playing and self.current_playlist:
                    self.current_index = (self.current_index + 1) % len(self.current_playlist)
                    pygame.time.wait(1000)  # Wait a second before trying next song
                else:
                    break
    
    def stop(self):
        if self.is_playing:
            stop_text = "🛑 Stopping playback"
            if self.is_shuffled:
                stop_text += " (shuffled)"
            print(f"{stop_text}...")
        
        self.is_playing = False
        self.is_shuffled = False
        pygame.mixer.music.stop()
        
        # Wait for playback thread to finish
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=2)
        
        self.current_playlist = []
        self.current_index = 0
    
    def get_current_song(self):
        if self.is_playing and self.current_playlist:
            return os.path.basename(self.current_playlist[self.current_index])
        return None