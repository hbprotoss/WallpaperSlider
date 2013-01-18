#!/usr/bin/env python

import subprocess
import os
import shlex
import urlparse

cmd = 'gsettings %s org.gnome.desktop.background picture-uri %s'

def getWallpaper():
    cmd_get = cmd % ('get', '')
    p = subprocess.Popen(cmd_get, stdout=subprocess.PIPE, shell=True)
    uri = p.stdout.read().strip('\n\'')
    path = urlparse.urlparse(uri).path
    return path

def setWallpaper(path):
    cmd_set = cmd % ('set', '"file://%s"' % path)
    os.system(cmd_set)
    
if(__name__ == '__main__'):
    print getWallpaper()
    path = raw_input()
    setWallpaper(path)