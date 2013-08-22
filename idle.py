#!/usr/bin/env python

import sys, time, os, ctypes
import commands

class XScreenSaverInfo(ctypes.Structure):
    """ typedef struct { ... } XScreenSaverInfo; """
    _fields_ = [('window',      ctypes.c_ulong), # screen saver window
                ('state',       ctypes.c_int),   # off,on,disabled
                ('kind',        ctypes.c_int),   # blanked,internal,external
                ('since',       ctypes.c_ulong), # milliseconds
                ('idle',        ctypes.c_ulong), # milliseconds
                ('event_mask',  ctypes.c_ulong)] # events
    def dance(self):
        xlib = ctypes.cdll.LoadLibrary('libX11.so.6')
        dpy = xlib.XOpenDisplay(os.environ['DISPLAY'])
        root = xlib.XDefaultRootWindow(dpy)
        xss = ctypes.cdll.LoadLibrary('libXss.so.1')
        xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
        xss_info = xss.XScreenSaverAllocInfo()

        status = commands.getoutput("cmus-remote -Q | grep status")

        xss.XScreenSaverQueryInfo(dpy, root, xss_info)
        idle_time_seconds = xss_info.contents.idle / 1000.0
        while True:
            try:
                xss.XScreenSaverQueryInfo(dpy, root, xss_info)
                idle_time_seconds = xss_info.contents.idle / 1000.0
                #os.system("echo %s - %s >> /tmp/debug" % (idle_time_seconds, xss_info.contents.idle))
                status = commands.getoutput("cmus-remote -Q | grep status")
                if idle_time_seconds > 30:
                    if status.find('play') > -1:
                        os.system("cmus-remote -u")
                        time.sleep(0.2)
                else:
                    if status.find('pause') > -1:
                        os.system("cmus-remote -u")
                        time.sleep(0.2)
            except KeyboardInterrupt:
                sys.exit(0)

if __name__ == "__main__":
    x = XScreenSaverInfo()
    x.dance()
