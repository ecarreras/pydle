#!/usr/bin/env python

import sys, time, os, ctypes
import subprocess
import argparse

try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False

class MusicPlayer(object):
    """Base class for music player controllers"""
    def __init__(self):
        pass
    
    def get_status(self):
        """Returns 'play', 'pause', or 'stopped'"""
        raise NotImplementedError
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        raise NotImplementedError

class CmusPlayer(MusicPlayer):
    """Controller for cmus music player"""
    def get_status(self):
        try:
            result = subprocess.run(['cmus-remote', '-Q'], 
                                  capture_output=True, text=True, timeout=5)
            status = result.stdout
            if 'playing' in status:
                return 'play'
            elif 'paused' in status:
                return 'pause'
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass
        return 'stopped'
    
    def toggle_play_pause(self):
        try:
            subprocess.run(['cmus-remote', '-u'], timeout=5)
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass

class RhythmboxPlayer(MusicPlayer):
    """Controller for Rhythmbox music player"""
    def get_status(self):
        try:
            result = subprocess.run(['rhythmbox-client', '--print-playing-format', '%st'],
                                  capture_output=True, text=True, timeout=5)
            status = result.stdout
            if 'Playing' in status:
                return 'play'
            elif 'Paused' in status:
                return 'pause'
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass
        return 'stopped'
    
    def toggle_play_pause(self):
        try:
            subprocess.run(['rhythmbox-client', '--play-pause'], timeout=5)
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass

class AudaciousPlayer(MusicPlayer):
    """Controller for Audacious music player"""
    def get_status(self):
        try:
            result = subprocess.run(['audacious', '--playback-status'],
                                  capture_output=True, text=True, timeout=5)
            status = result.stdout
            if 'playing' in status:
                return 'play'
            elif 'paused' in status:
                return 'pause'
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass
        return 'stopped'
    
    def toggle_play_pause(self):
        try:
            subprocess.run(['audacious', '--play-pause'], timeout=5)
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass

class IdleMonitor(object):
    """Base class for idle time monitors"""
    def get_idle_time(self):
        """Returns idle time in seconds"""
        raise NotImplementedError
    
    def monitor(self, player, idle_threshold=30):
        """Monitor idle time and control player"""
        while True:
            try:
                idle_time_seconds = self.get_idle_time()
                status = player.get_status()
                if idle_time_seconds > idle_threshold:
                    if status == 'play':
                        player.toggle_play_pause()
                        time.sleep(0.2)
                else:
                    if status == 'pause':
                        player.toggle_play_pause()
                        time.sleep(0.2)
                time.sleep(1)
            except KeyboardInterrupt:
                sys.exit(0)

class XScreenSaverInfo(ctypes.Structure):
    """ typedef struct { ... } XScreenSaverInfo; """
    _fields_ = [('window',      ctypes.c_ulong), # screen saver window
                ('state',       ctypes.c_int),   # off,on,disabled
                ('kind',        ctypes.c_int),   # blanked,internal,external
                ('since',       ctypes.c_ulong), # milliseconds
                ('idle',        ctypes.c_ulong), # milliseconds
                ('event_mask',  ctypes.c_ulong)] # events

class X11IdleMonitor(IdleMonitor):
    """Idle monitor for X11 using XScreenSaver extension"""
    def __init__(self):
        try:
            self.xlib = ctypes.cdll.LoadLibrary('libX11.so.6')
            self.dpy = self.xlib.XOpenDisplay(os.environ.get('DISPLAY', ':0'))
            self.root = self.xlib.XDefaultRootWindow(self.dpy)
            self.xss = ctypes.cdll.LoadLibrary('libXss.so.1')
            self.xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
            self.xss_info = self.xss.XScreenSaverAllocInfo()
        except (OSError, KeyError) as e:
            raise RuntimeError(f"Failed to initialize X11 idle monitor: {e}")
    
    def get_idle_time(self):
        self.xss.XScreenSaverQueryInfo(self.dpy, self.root, self.xss_info)
        return self.xss_info.contents.idle / 1000.0

class DBusIdleMonitor(IdleMonitor):
    """Idle monitor using D-Bus (works on both X11 and Wayland)"""
    def __init__(self):
        if not DBUS_AVAILABLE:
            raise RuntimeError("D-Bus is not available. Install python3-dbus or dbus-python package.")
        
        try:
            self.bus = dbus.SessionBus()
            self.last_input_time = time.time()
            
            # Try to connect to org.freedesktop.ScreenSaver for idle detection
            # This is supported by most desktop environments
            self.screensaver = self.bus.get_object('org.freedesktop.ScreenSaver', '/org/freedesktop/ScreenSaver')
            self.screensaver_iface = dbus.Interface(self.screensaver, 'org.freedesktop.ScreenSaver')
        except dbus.exceptions.DBusException:
            # Fallback: use a simple time-based approach
            self.screensaver = None
            self.screensaver_iface = None
    
    def get_idle_time(self):
        if self.screensaver_iface:
            try:
                # GetSessionIdleTime returns milliseconds
                idle_ms = self.screensaver_iface.GetSessionIdleTime()
                return idle_ms / 1000.0
            except dbus.exceptions.DBusException:
                pass
        
        # Fallback: return 0 (not idle) - this is a limitation without proper idle detection
        return 0

PLAYERS = {
    'cmus': CmusPlayer,
    'rhythmbox': RhythmboxPlayer,
    'audacious': AudaciousPlayer,
}

def detect_session_type():
    """Detect if running on X11 or Wayland"""
    session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
    if session_type == 'wayland':
        return 'wayland'
    elif session_type == 'x11':
        return 'x11'
    
    # Fallback detection
    if os.environ.get('WAYLAND_DISPLAY'):
        return 'wayland'
    elif os.environ.get('DISPLAY'):
        return 'x11'
    
    return 'unknown'

def create_idle_monitor(prefer_x11=False):
    """Create appropriate idle monitor based on session type"""
    session = detect_session_type()
    
    # Try X11 first if preferred or on X11 session
    if prefer_x11 or session == 'x11':
        try:
            return X11IdleMonitor()
        except RuntimeError as e:
            if session == 'x11':
                print(f"Warning: X11 monitor failed: {e}", file=sys.stderr)
    
    # Try D-Bus monitor (works on both X11 and Wayland)
    if DBUS_AVAILABLE:
        try:
            return DBusIdleMonitor()
        except RuntimeError as e:
            print(f"Warning: D-Bus monitor failed: {e}", file=sys.stderr)
    
    # Last resort: try X11 again
    try:
        return X11IdleMonitor()
    except RuntimeError as e:
        print(f"Error: Could not initialize any idle monitor: {e}", file=sys.stderr)
        print("Please ensure either X11 libraries (libX11, libXss) or D-Bus (python3-dbus) are installed.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Automatically pause/resume music player when idle')
    parser.add_argument('--player', '-p', 
                        choices=PLAYERS.keys(),
                        default='cmus',
                        help='Music player to control (default: cmus)')
    parser.add_argument('--idle-time', '-t',
                        type=int,
                        default=30,
                        help='Idle time threshold in seconds (default: 30)')
    parser.add_argument('--force-x11', action='store_true',
                        help='Force use of X11 idle detection even on Wayland')
    
    args = parser.parse_args()
    
    player_class = PLAYERS[args.player]
    player = player_class()
    
    monitor = create_idle_monitor(prefer_x11=args.force_x11)
    print(f"Using {monitor.__class__.__name__} for idle detection", file=sys.stderr)
    
    monitor.monitor(player, args.idle_time)
