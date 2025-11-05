# pydle - Automatic Music Player Pause on Idle

A Python script that automatically pauses your music player when you're idle and resumes it when you come back.

## Features

- Monitors X11 idle time using XScreenSaver
- Automatically pauses music when idle for more than 30 seconds (configurable)
- Automatically resumes music when you return
- Supports multiple music players:
  - **cmus** (default)
  - **Rhythmbox**
  - **Audacious**
  - **Spotify** (via D-Bus/MPRIS)

## Requirements

- Python 3.x
- Linux (X11 or Wayland)
- For X11: libX11.so.6 and libXss.so.1
- For Wayland (or X11 alternative): python3-dbus (dbus-python)
- For Spotify: python3-dbus (dbus-python) - required for MPRIS control
- One of the supported music players installed

## Usage

### Basic usage (defaults to cmus):
```bash
python idle.py
```

### Specify a different music player:
```bash
# For Rhythmbox
python idle.py --player rhythmbox

# For Audacious
python idle.py --player audacious

# For Spotify
python idle.py --player spotify
```

### Customize idle time threshold:
```bash
# Pause after 60 seconds of inactivity
python idle.py --idle-time 60

# Combine player and idle time options
python idle.py --player rhythmbox --idle-time 45
```

### Force X11 idle detection (on Wayland):
```bash
# Use X11 idle detection even on Wayland (if XWayland is available)
python idle.py --force-x11
```

### Command-line options:
```
usage: idle.py [-h] [--player {cmus,rhythmbox,audacious,spotify}] [--idle-time IDLE_TIME] [--force-x11]

Automatically pause/resume music player when idle

options:
  -h, --help            show this help message and exit
  --player {cmus,rhythmbox,audacious,spotify}, -p {cmus,rhythmbox,audacious,spotify}
                        Music player to control (default: cmus)
  --idle-time IDLE_TIME, -t IDLE_TIME
                        Idle time threshold in seconds (default: 30)
  --force-x11           Force use of X11 idle detection even on Wayland
```

## Installation

1. Clone this repository:
```bash
git clone https://github.com/ecarreras/pydle.git
cd pydle
```

2. Make the script executable (optional):
```bash
chmod +x idle.py
```

3. Run it:
```bash
python idle.py --player rhythmbox
```

## How It Works

The script monitors system idle time and automatically controls your music player. When you're idle for longer than the threshold:
1. It checks if your music player is currently playing
2. If playing, it pauses the music
3. When you return (idle time drops below threshold), it resumes playback

### Display Server Support

The script automatically detects your display server and uses the appropriate idle detection method:

- **X11**: Uses XScreenSaver extension (libXss) for accurate idle time detection
- **Wayland**: Uses D-Bus (`org.freedesktop.ScreenSaver`) for idle time detection
- **Automatic detection**: The script will try D-Bus first on Wayland, falling back to X11 if needed
- **Override**: Use `--force-x11` to force X11 idle detection (useful on Wayland with XWayland)

## Player Support

### cmus
- Status command: `cmus-remote -Q | grep status`
- Toggle command: `cmus-remote -u`

### Rhythmbox
- Status command: `rhythmbox-client --print-playing-format '%st'`
- Toggle command: `rhythmbox-client --play-pause`

### Audacious
- Status command: `audacious --playback-status`
- Toggle command: `audacious --play-pause`

### Spotify
- Uses D-Bus MPRIS interface (`org.mpris.MediaPlayer2.spotify`)
- Requires: python3-dbus (dbus-python)
- Status: Reads `PlaybackStatus` property
- Toggle: Calls `PlayPause` method

## Extending

To add support for additional music players, create a new class that inherits from `MusicPlayer`:

```python
class MyPlayerName(MusicPlayer):
    def get_status(self):
        # Return 'play', 'pause', or 'stopped'
        status = subprocess.getoutput("myplayer-cli status")
        if 'playing' in status:
            return 'play'
        elif 'paused' in status:
            return 'pause'
        return 'stopped'
    
    def toggle_play_pause(self):
        os.system("myplayer-cli toggle")
```

Then add it to the `PLAYERS` dictionary:
```python
PLAYERS = {
    'cmus': CmusPlayer,
    'rhythmbox': RhythmboxPlayer,
    'audacious': AudaciousPlayer,
    'myplayer': MyPlayerName,
}
```

## License

See repository for license information.
