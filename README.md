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

## Requirements

- Python 3.x
- X11 environment (Linux)
- libX11.so.6
- libXss.so.1
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
```

### Customize idle time threshold:
```bash
# Pause after 60 seconds of inactivity
python idle.py --idle-time 60

# Combine player and idle time options
python idle.py --player rhythmbox --idle-time 45
```

### Command-line options:
```
usage: idle.py [-h] [--player {cmus,rhythmbox,audacious}] [--idle-time IDLE_TIME]

Automatically pause/resume music player when idle

options:
  -h, --help            show this help message and exit
  --player {cmus,rhythmbox,audacious}, -p {cmus,rhythmbox,audacious}
                        Music player to control (default: cmus)
  --idle-time IDLE_TIME, -t IDLE_TIME
                        Idle time threshold in seconds (default: 30)
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

The script uses the XScreenSaver extension to monitor system idle time. When you're idle for longer than the threshold:
1. It checks if your music player is currently playing
2. If playing, it pauses the music
3. When you return (idle time drops below threshold), it resumes playback

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
