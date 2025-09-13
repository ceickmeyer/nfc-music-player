# NFC Music Player for Raspberry Pi

An NFC-controlled music player that plays albums from a USB drive when you place NFC stickers on an RC522 reader. Perfect for creating a physical music collection that anyone can use!

## ✨ Features

- **Physical Music Control**: Place NFC stickers to instantly play albums
- **Shuffle Support**: Configure albums to play in shuffled order
- **Plug & Play**: Just connect your USB drive with MP3 albums
- **Activity Logging**: Track what's been played and when
- **Auto-start**: Runs automatically on boot
- **Simple Setup**: Interactive configuration tool included

## 🛠 Hardware Requirements

- Raspberry Pi 3 or newer
- RC522 RFID/NFC Reader module
- NFC stickers/tags (NTAG213 recommended)
- USB drive with MP3 albums
- 3.5mm speakers or headphones
- Jumper wires for connections

## 🔌 Wiring Diagram

Connect the RC522 to your Raspberry Pi:

| RC522 Pin | Raspberry Pi Pin | GPIO |
|-----------|------------------|------|
| SDA/SS    | Pin 24          | GPIO 8 |
| SCK       | Pin 23          | GPIO 11 |
| MOSI      | Pin 19          | GPIO 10 |
| MISO      | Pin 21          | GPIO 9 |
| IRQ       | Not connected   | - |
| GND       | Pin 6           | Ground |
| RST       | Pin 22          | GPIO 25 |
| 3.3V      | Pin 1           | 3.3V |

## 📁 USB Drive Setup

Organize your music like this:

```
USB_Drive/
├── Album 1/
│   ├── 01-song1.mp3
│   ├── 02-song2.mp3
│   └── 03-song3.mp3
├── Album 2/
│   ├── track01.mp3
│   └── track02.mp3
└── Greatest Hits/
    ├── hit1.mp3
    └── hit2.mp3
```

- Each folder = one album
- Only MP3 files supported
- Files play in alphabetical order (unless shuffled)

## 🚀 Installation

### 1. Enable SPI
```bash
sudo raspi-config
# Navigate to: Interface Options > SPI > Enable
sudo reboot
```

### 2. Install Dependencies
```bash
sudo apt update
sudo apt install python3-pip git
sudo pip3 install mfrc522 pygame mutagen
```

### 3. Clone Repository
```bash
cd ~
git clone https://github.com/yourusername/nfc-music-player.git
cd nfc-music-player
```

### 4. Test Hardware
```bash
# Test NFC reader
python3 test_rfid.py

# Test USB drive detection
python3 test_usb.py
```

### 5. Configure Albums & NFC Tags
```bash
python3 generate_config.py
```

This interactive tool will:
- Find your USB drive and scan for albums
- Let you map NFC stickers to specific albums
- Ask if you want each album to play shuffled
- Create the configuration file

### 6. Test the System
```bash
python3 main.py
```

Place your configured NFC stickers on the reader to test!

### 7. Set Up Auto-Start
```bash
sudo cp nfc-music.service /etc/systemd/system/
sudo systemctl enable nfc-music.service
sudo systemctl start nfc-music.service
```

## 🎵 Usage

1. **Play Music**: Place any configured NFC sticker on the reader
2. **Stop Music**: Remove the sticker from the reader
3. **Switch Albums**: Remove current sticker and place a different one
4. **Check Logs**: View `logs/activity.log` for play history

## ⚙️ Configuration

The `config.json` file stores your settings:

```json
{
  "usb_mount_path": "/media/cody/MUSIC",
  "nfc_mappings": {
    "123456789": {
      "album": "Greatest Hits",
      "shuffle": false
    },
    "987654321": {
      "album": "Dance Party",
      "shuffle": true
    }
  },
  "audio_settings": {
    "volume": 0.7
  }
}
```

### Adding New NFC Tags

1. Run the system and place a new NFC sticker on the reader
2. Check console output or `logs/activity.log` for the NFC ID
3. Either:
   - Re-run `python3 generate_config.py` to add it interactively
   - Or manually edit `config.json` and restart the service

## 🔧 Troubleshooting

### No Audio Output
```bash
# Check audio devices
aplay -l

# Set to 3.5mm jack
sudo amixer cset numid=3 1

# Set to HDMI
sudo amixer cset numid=3 2

# Adjust volume
alsamixer
```

### NFC Not Reading
- Verify all wiring connections
- Ensure SPI is enabled: `sudo raspi-config`
- Try different NFC stickers
- Check with: `python3 test_rfid.py`

### USB Drive Not Found
- Check mount point: `lsblk`
- Update `usb_mount_path` in config.json
- Ensure drive is FAT32 formatted
- Test with: `python3 test_usb.py`

### Service Not Starting
```bash
# Check service status
sudo systemctl status nfc-music.service

# View logs
sudo journalctl -u nfc-music.service -f

# Restart service
sudo systemctl restart nfc-music.service
```

## 📊 Activity Logging

All activity is logged to `logs/activity.log`:

```
2024-01-15 14:30:25 | NFC: 123456789 | Album: Greatest Hits | Action: started
2024-01-15 14:35:12 | NFC: 123456789 | Album: Greatest Hits | Action: stopped
2024-01-15 14:36:45 | NFC: 987654321 | Album: Dance Party | Action: started_shuffled
```

## 🎯 Project Structure

```
nfc-music-player/
├── main.py                 # Main application
├── generate_config.py      # Interactive setup tool
├── config.json            # NFC mappings and settings
├── music_player.py        # Audio playback handler
├── nfc_reader.py          # NFC reading functionality
├── logger.py              # Activity logging
├── test_rfid.py           # Hardware test utility
├── test_usb.py            # USB detection test
├── nfc-music.service      # Systemd service file
├── logs/
│   └── activity.log       # Play history
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Uses the [mfrc522 library](https://github.com/pimylifeup/MFRC522-python) for NFC reading
- Built with [pygame](https://pygame.org) for audio playback
- Inspired by vinyl record players and physical music collections

---

**Enjoy your physical digital music collection! 🎶**