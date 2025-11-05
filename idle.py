#!/usr/bin/env python

import sys, time, os, ctypes
import subprocess
import argparse

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
            status = subprocess.getoutput("cmus-remote -Q | grep status")
            if status.find('playing') > -1:
                return 'play'
            elif status.find('paused') > -1:
                return 'pause'
        except:
            pass
        return 'stopped'
    
    def toggle_play_pause(self):
        os.system("cmus-remote -u")

class RhythmboxPlayer(MusicPlayer):
    """Controller for Rhythmbox music player"""
    def get_status(self):
        try:
            status = subprocess.getoutput("rhythmbox-client --print-playing-format '%st'")
            if status.find('Playing') > -1:
                return 'play'
            elif status.find('Paused') > -1:
                return 'pause'
        except:
            pass
        return 'stopped'
    
    def toggle_play_pause(self):
        os.system("rhythmbox-client --play-pause")

class AudaciousPlayer(MusicPlayer):
    """Controller for Audacious music player"""
    def get_status(self):
        try:
            status = subprocess.getoutput("audacious --playback-status")
            if status.find('playing') > -1:
                return 'play'
            elif status.find('paused') > -1:
                return 'pause'
        except:
            pass
        return 'stopped'
    
    def toggle_play_pause(self):
        os.system("audacious --play-pause")

class XScreenSaverInfo(ctypes.Structure):
    """ typedef struct { ... } XScreenSaverInfo; """
    _fields_ = [('window',      ctypes.c_ulong), # screen saver window
                ('state',       ctypes.c_int),   # off,on,disabled
                ('kind',        ctypes.c_int),   # blanked,internal,external
                ('since',       ctypes.c_ulong), # milliseconds
                ('idle',        ctypes.c_ulong), # milliseconds
                ('event_mask',  ctypes.c_ulong)] # events
    
    def dance(self, player, idle_threshold=30):
        xlib = ctypes.cdll.LoadLibrary('libX11.so.6')
        dpy = xlib.XOpenDisplay(os.environ['DISPLAY'])
        root = xlib.XDefaultRootWindow(dpy)
        xss = ctypes.cdll.LoadLibrary('libXss.so.1')
        xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
        xss_info = xss.XScreenSaverAllocInfo()

        xss.XScreenSaverQueryInfo(dpy, root, xss_info)
        idle_time_seconds = xss_info.contents.idle / 1000.0
        while True:
            try:
                xss.XScreenSaverQueryInfo(dpy, root, xss_info)
                idle_time_seconds = xss_info.contents.idle / 1000.0
                #os.system("echo %s - %s >> /tmp/debug" % (idle_time_seconds, xss_info.contents.idle))
                status = player.get_status()
                if idle_time_seconds > idle_threshold:
                    if status == 'play':
                        player.toggle_play_pause()
                        time.sleep(0.2)
                else:
                    if status == 'pause':
                        player.toggle_play_pause()
                        time.sleep(0.2)
            except KeyboardInterrupt:
                sys.exit(0)

PLAYERS = {
    'cmus': CmusPlayer,
    'rhythmbox': RhythmboxPlayer,
    'audacious': AudaciousPlayer,
}

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
    
    args = parser.parse_args()
    
    player_class = PLAYERS[args.player]
    player = player_class()
    
    x = XScreenSaverInfo()
    x.dance(player, args.idle_time)
