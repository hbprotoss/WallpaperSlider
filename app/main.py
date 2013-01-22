#!/usr/bin/env python

import gtk, gobject
import argparse
import os, sys
import urllib
import threading
import time
import ConfigParser

import wallpaper

GLADE = 'ui/app.glade'
DEFAULT_PATH = os.path.expanduser( '~/Wallpapers' )
CONFIG_FILE = os.path.expanduser('~/.config/WallpaperSlider/conf.ini')
SECTION_NAME = 'Wallpaper Slider'
IMAGE_EXT = ['jpeg', 'jpg', 'png', 'bmp', 'gif']

class Configure(ConfigParser.ConfigParser):
    def optionsxfor(self, option):
        return option
    
class WallpaperApp:
    menu = None
    menu_slide = None
    statusicon = None
    parameter = None
    wallpapers = None
    current_index = None
    
    # Mark whether the running status is changed.
    status_changed = False
    event = threading.Event()
    running = True
    
    # Essential parameter
    directory = None
    interval_time = None
    
    def __init__( self ):
        parameters = self.initParser()
        self.initParameters(parameters)
        
        # Loading UI from glade       
        signal = {
                  'on_menu_about_activate': self.aboutDialog,
                  'on_menu_slide_activate': self.StartOrStop,
                  'on_menu_previous_activate': self.previousWallpaper,
                  'on_menu_next_activate': self.nextWallpaper,
                  'on_menu_quit_activate': self.Quit
                  }
        glade = gtk.Builder()
        glade.add_from_file(GLADE)
        glade.connect_signals(signal)
        
        self.statusicon = self.initStatusIcon()
        self.menu = glade.get_object('menu_popup')
        self.menu_slide = glade.get_object('menu_slide')
        self.menu_slide.set_use_stock(True)
        # TODO:Bugs after recover from Pause state, so disable the menu temporary
        # self.menu_slide.set_sensitive(False)
        
        # Retrieve all files in wallpaper dir
        self.wallpapers = [os.path.join(self.directory, file) 
                for file in sorted(os.listdir(self.directory))
                if file.rsplit('.', 1)[-1].lower() in IMAGE_EXT
                ]
        current = urllib.unquote(wallpaper.getWallpaper())
        print 'Current wallpaper: ', current

        # Set current wallpaper file index
        try:
            self.current_index = self.wallpapers.index(current)
        except ValueError:
            self.current_index = 0
            
        # Start to change wallpaper automatically
        self.startTimer()
        
        self._printParam(True)
            
    def _printParam(self, init = False):
        if(init):
	        print self.directory, self.interval_time
        print self.wallpapers[self.current_index]
        print 'Playing:', self.running

    def initParameters(self, parameters):
        conf = Configure()
        conf.add_section(SECTION_NAME)
        # Read from conf file
        try:
            conf.read(CONFIG_FILE)
            self.directory = os.path.expanduser(conf.get(SECTION_NAME, 'directory'))
            self.interval_time = conf.getint(SECTION_NAME, 'interval_time')
        except:
            self.directory = self.interval_time = None
            pass

        # Parse command line parameter
        if(parameters.directory is not None):
            self.directory = os.path.expanduser(parameters.directory)
        if(parameters.interval_time is not None):
            self.interval_time = parameters.interval_time

        if((self.directory is None) or (self.interval_time is None) ):
            print self.directory, self.interval_time
            raise Exception('Parameters error. Please refer to README.')

        # Record to conf file
        dirname = os.path.dirname(CONFIG_FILE)
        if(not os.path.exists(dirname)):
            os.makedirs(dirname)
        conf.set(SECTION_NAME, 'directory', self.directory)
        conf.set(SECTION_NAME, 'interval_time', self.interval_time)
        conf.write(open(CONFIG_FILE, 'w'))
    
    def initStatusIcon(self):
        statusicon = gtk.StatusIcon()
        statusicon.set_from_stock(gtk.STOCK_HOME)
        statusicon.connect('popup-menu', self.rightClickEvent)
        statusicon.set_tooltip('Wallpaper Slider')
        
        return statusicon

    def initParser( self ):
        parser = argparse.ArgumentParser( description = 'Wallpaper Slider' )
        parser.add_argument( '-d', '--directory', dest = 'directory', help = 'The directory of wallpapers' )
        parser.add_argument( '-t', '--time', dest = 'interval_time', type = int, help = 'The interval time between two wallpapers(in minute)' )
        return parser.parse_args()
    
    def startTimer(self):
        def worker():
            while(True):
                self.event.wait(self.interval_time * 60)

                # Polling wait
                while(not self.running):
                    time.sleep(0.5)
                
                # If recover from pause status, wait another cycle
                if(self.status_changed):
                    self.event.wait(self.interval_time * 60)
                self.nextWallpaper()
                
        self.running = True
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
    
    def StartOrStop(self, widget = None):
        if(self.running):
            # Going to pause
            self.menu_slide.get_image().set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_MENU)
            self.menu_slide.set_label('Play')
            self.status_changed = True
            self.running = False
        else:
            # Going to play
            self.menu_slide.get_image().set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_MENU)
            self.menu_slide.set_label('Pause')
            self.status_changed = True
            self.running = True
    
    def Quit(self, widget=None):
        print 'Quit...'
        self.running = False
        gtk.main_quit()
    
    def nextWallpaper(self, widget=None):
        self.current_index = (self.current_index + 1) % len(self.wallpapers)
        wallpaper.setWallpaper(self.wallpapers[self.current_index])
        self.status_changed = False
        self._printParam()
        
    def previousWallpaper(self, widget=None):
        self.current_index = (self.current_index - 1) % len(self.wallpapers)
        wallpaper.setWallpaper(self.wallpapers[self.current_index])
        self.status_changed = False
        self._printParam()
    
    def rightClickEvent(self, icon, button, time):
        self.menu.show_all()
        self.menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusicon)
    
    def aboutDialog(self, widget=None):
		about_dialog = gtk.AboutDialog()
		
		about_dialog.set_name("Wallpaper Slider")
		about_dialog.set_version("0.1")
		about_dialog.set_authors(["hbprotoss"])
		
		about_dialog.run()
		about_dialog.destroy()

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
WallpaperApp()
gobject.threads_init()
gtk.main()
