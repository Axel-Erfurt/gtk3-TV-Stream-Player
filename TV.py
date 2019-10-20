#!/usr/bin/python3
# -*- coding: utf-8 -*-
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version('Gdk', '3.0')
gi.require_version('Notify', '0.7')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, Gdk, Gst, Notify, AppIndicator3 as tray
from os import path
from sys import argv
from requests import get as getURL

Gst.init(None)
Gst.init_check(None)

class PlayerWidget(Gtk.Box):
    def __init__(self, parent):
        super(PlayerWidget, self).__init__()
        self.parent = parent
        self.player = Gst.ElementFactory.make("playbin", "player")

        self.connect('realize', self.on_realize_gst)

    def on_realize_gst(self, widget):
        playerFactory = self.player.get_factory()
        gtksink = playerFactory.make('gtksink')
        self.player.set_property("video-sink", gtksink)

        self.pack_start(gtksink.props.widget, True, True, 0)
        gtksink.props.widget.show()


class VideoDialog(Gtk.Window):
    def __init__(self, parent=None):
        super(VideoDialog, self).__init__()

        img = "computer"
        self.set_icon_name(img)
        self.set_decorated(False)
        self.set_keep_above(True) 
        self.set_border_width(0)
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))

        self.set_default_size(500, 500 / 1.777777778)

        self.playerWidget = PlayerWidget(self)
        self.playerWidget.set_vexpand(True)
        self.playerWidget.set_hexpand(True)

        self.player = self.playerWidget.player

        self.add(self.playerWidget)

        self.set_events (Gdk.EventMask.ALL_EVENTS_MASK)
        self.connect("destroy",Gtk.main_quit)
        self.connect('scroll-event', self.my_zoom)
        self.connect("window-state-event", self.on_window_state_event)
        self.connect('key_release_event', self.on_key_press_event)
        self.connect('button_press_event', self.on_button_press_event)
        self.connect('motion_notify_event', self.on_motion_notify_event)

        self.channel = 0
        self.HD = False

        Notify.init("TV")

        self.show_all()
        self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))

        ### SD List
        self.channelsfile = path.join(path.dirname(argv[0]), "channels.txt")

        if path.exists(self.channelsfile) == True:
            with open(self.channelsfile, 'r') as f:
                self.chlist = f.read().splitlines()
            self.ch_names = []
            self.ch_urls = []
            for line in self.chlist:
                self.ch_names.append(line.partition(",")[0])
                self.ch_urls.append(line.partition(",")[2])

        ### HD List
        self.channelsfileHD = path.join(path.dirname(argv[0]), "channelsHD.txt")

        if path.exists(self.channelsfileHD) == True:
            with open(self.channelsfileHD, 'r') as f:
                self.chlistHD = f.read().splitlines()
            self.ch_namesHD = []
            self.ch_urlsHD = []
            for line in self.chlistHD:
                self.ch_namesHD.append(line.partition(",")[0])
                self.ch_urlsHD.append(line.partition(",")[2])

    def getSport1(self, *args):
        url = "https://tv.sport1.de/sport1/"
        r = getURL(url)
        t = r.text.partition('file: "')[2].partition('"')[0]
        self.playTV(t)

    def item_activated(self, wdg, i):
        print("%s:%s '%s'" %('Channel', i, self.ch_names[i - 1]))
        self.channel = i
        Notify.Notification.new(self.ch_names[i - 1]).show()
        self.playTV(self.ch_urls[i - 1])
        self.HD = False

    def item_activatedHD(self, wdg, i):
        print("%s:%s '%s'" %('Channel', i, self.ch_namesHD[i - 1]))
        self.channel = i
        Notify.Notification.new(self.ch_namesHD[i - 1]).show()
        self.playTV(self.ch_urlsHD[i - 1])
        self.HD = True

    def create_menu(self):
        self.action_channelsmenu = Gtk.Menu()

        img = Gtk.Image()
        img.set_from_icon_name("window-close", 20)
        self.action_filequit = Gtk.ImageMenuItem("Quit")
        self.action_filequit.connect("activate", Gtk.main_quit)
        self.action_filequit.set_image(img)
        self.action_channelsmenu.append(self.action_filequit)

        sep = Gtk.SeparatorMenuItem()
        self.action_channelsmenu.append(sep)

        img = Gtk.Image()
        img.set_from_icon_name("browser", 20)
        self.action_clip = Gtk.ImageMenuItem("play URL from clipboard")
        self.action_clip.connect("activate", self.playClipboardURL)
        self.action_clip.set_image(img)
        self.action_channelsmenu.append(self.action_clip)

        sep = Gtk.SeparatorMenuItem()
        self.action_channelsmenu.append(sep)

        ### HD Submenu
        img = Gtk.Image()
        img.set_from_icon_name("video-display", 20)
        HDMenu = Gtk.ImageMenuItem()
        HDMenu.set_label("HD")
        HDMenu.set_image(img)
        self.action_channelsmenu.append(HDMenu)

        self.sub_menu = Gtk.Menu()

        ### HD
        for x in range(1, len(self.chlistHD) + 1):
            img = Gtk.Image()
            img.set_from_icon_name("video-display", 20)
            action_channelHD = Gtk.ImageMenuItem(self.ch_namesHD[x - 1])
            action_channelHD.set_image(img)
            self.sub_menu.append(action_channelHD)
            action_channelHD.connect("activate", self.item_activatedHD, x)

        HDMenu.set_submenu(self.sub_menu)

        ### SD
        for x in range(1, len(self.chlist) + 1):
            img = Gtk.Image()
            img.set_from_icon_name("computer", 20)
            action_channel = Gtk.ImageMenuItem(self.ch_names[x - 1])
            action_channel.set_image(img)
            self.action_channelsmenu.append(action_channel)
            action_channel.connect("activate", self.item_activated, x)

        img = Gtk.Image()
        img.set_from_icon_name("computer", 20)
        action_sport1 = Gtk.ImageMenuItem("Sport 1")
        action_sport1.set_image(img)
        self.action_channelsmenu.append(action_sport1)
        action_sport1.connect("activate", self.getSport1)

        self.action_channelsmenu.show_all()
        return self.action_channelsmenu

    def msg(self):
        infotext = ("©2019 Axel Schneider\n\nShortcuts:\nArrow Left -> Volume down\nArrow Right -> Volume up \
             \nArrow Up -> Channel up\nArrow Down -> Channel down\nKey(1-9) -> Channel (1-9) \
             \nmouse wheel -> zoom in/out \
              \nu -> play URL from clipboard \
              \nm -> toggle mute\nf -> toggle fullscreen\nq -> Quit")
        print(infotext)
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, "TV Player")
        dialog.format_secondary_text(infotext)
        dialog.run()
        print("INFO dialog closed")

        dialog.destroy()

    def on_motion_notify_event(self, widget, motion):
        if ((motion.state and Gdk.ModifierType.BUTTON1_MASK) == Gdk.ModifierType.BUTTON1_MASK):
            x = self.get_position()[0]
            y = self.get_position()[1]
            self.move(x + motion.x, y + motion.y)
            return False

    def on_button_press_event(self, widget, button):
        if (button.button == 1): ## left mouse button
            self.last_x = button.x
            self.last_y = button.y
            return True
        elif (button.button == 3): ## right mouse button
            self.action_channelsmenu.show_all()
            self.action_channelsmenu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
        else:
            return False

    def playClipboardURL(self, *args):
        c = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        url = c.wait_for_text()
        if path.isfile(url):
            url = "%s%s" % ("file://", url)
        print(url)
        self.playTV(url)

    def on_key_press_event(self, widget, event):
        if self.HD == False:
            if event.keyval == Gdk.KEY_1:
                self.item_activated(self, 1)
            elif event.keyval == Gdk.KEY_2:
                self.item_activated(self, 2)
            elif event.keyval == Gdk.KEY_3:
                self.item_activated(self, 3)
            elif event.keyval == Gdk.KEY_4:
                self.item_activated(self, 4)
            elif event.keyval == Gdk.KEY_5:
                self.item_activated(self, 5)
            elif event.keyval == Gdk.KEY_6:
                self.item_activated(self, 6)
            elif event.keyval == Gdk.KEY_7:
                self.item_activated(self, 7)
            elif event.keyval == Gdk.KEY_8:
                self.item_activated(self, 8)
            elif event.keyval == Gdk.KEY_9:
                self.item_activated(self, 9)
            elif event.keyval == Gdk.KEY_0:
                self.item_activated(self, 10)
        else:
            if event.keyval == Gdk.KEY_1:
                self.item_activatedHD(self, 1)
            elif event.keyval == Gdk.KEY_2:
                self.item_activatedHD(self, 2)
            elif event.keyval == Gdk.KEY_3:
                self.item_activatedHD(self, 3)
            elif event.keyval == Gdk.KEY_4:
                self.item_activatedHD(self, 4)
            elif event.keyval == Gdk.KEY_5:
                self.item_activatedHD(self, 5)
            elif event.keyval == Gdk.KEY_6:
                self.item_activatedHD(self, 6)
            elif event.keyval == Gdk.KEY_7:
                self.item_activatedHD(self, 7)
            elif event.keyval == Gdk.KEY_8:
                self.item_activatedHD(self, 8)
            elif event.keyval == Gdk.KEY_9:
                self.item_activatedHD(self, 9)
            elif event.keyval == Gdk.KEY_0:
                self.item_activatedHD(self, 10)
        if event.keyval == Gdk.KEY_f:
            self.showFullScreen()
        elif event.keyval == Gdk.KEY_F1:
            self.msg()
        elif event.keyval == Gdk.KEY_m:
            self.toggleMute()
        elif event.keyval == 65361:
            self.lessVolume()
        elif event.keyval == 65363:
            self.moreVolume()
        elif event.keyval == 65362:
            self.channelUp()
        elif event.keyval == 65364:
            self.channelDown()
        elif event.keyval == Gdk.KEY_q:
            self.handleClose()
        elif event.keyval == Gdk.KEY_u:
            self.playClipboardURL()

    def channelUp(self):
        if self.HD == False:
            if self.channel < len(self.ch_names):
                self.channel = self.channel + 1
                self.item_activated(self, self.channel)
        else:
            if self.channel < len(self.ch_namesHD):
                self.channel = self.channel + 1
                self.item_activatedHD(self, self.channel)

    def channelDown(self):
        if self.HD == False:
            if self.channel > 1:
                self.channel = self.channel - 1
                self.item_activated(self, self.channel)
        else:
            if self.channel > 1:
                self.channel = self.channel - 1
                self.item_activatedHD(self, self.channel)

    def moreVolume(self):
        v = float(self.player.get_property("volume"))
        if v < 1.0:
            v = v + 0.1
            self.player.set_property("volume", v)
            print("changed volume to", v)

    def lessVolume(self):
        v = float(self.player.get_property("volume"))
        if v > 0.1:
            v = v - 0.1
            self.player.set_property("volume", v)
            print("changed volume to", v)

    def on_window_state_event(self, widget, ev):
        self.__is_fullscreen = bool(ev.new_window_state & Gdk.WindowState.FULLSCREEN)

    def my_zoom(self, widget, event):
        w = self.get_size()[0]
        h = self.get_size()[1]
        direction = event.get_scroll_deltas()[2]
        if direction < 0:
            if not w > 1250:
                self.resize(w + 30, (w + 30) / 1.777777778)
        elif direction > 0:
            if not w < 260:
                self.resize(w - 30, (w - 30) / 1.777777778)

    def handleClose(self):
        Notify.Notification.new("Goodbye ...").show()
        Gtk.main_quit()

    def playTV(self, url, *args):
        self.player.set_state(Gst.State.NULL)
        print("url=", url)
        self.player.set_property("uri", url)
        self.player.set_property("buffer-size", 3*1048576) # 3MB
        self.player.set_state(Gst.State.PLAYING)

    def toggleMute(self):
        if self.player.get_property("mute") == False:
            self.player.set_property("mute", True)
            print("muted")
        else:
            self.player.set_property("mute", False)
            print("unmuted")

    def showFullScreen(self):
        if self.__is_fullscreen:
            self.unfullscreen()
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))
            print("fullscreen deactivated")
        else:
            self.fullscreen()
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR))
            print("fullscreen activated")

    def on_window_state_event(self, widget, ev):
        self.__is_fullscreen = bool(ev.new_window_state & Gdk.WindowState.FULLSCREEN)


win = VideoDialog()
print("Welcome to gtk TV Player")
indicator = tray.Indicator.new("TV Tray", "computer", tray.IndicatorCategory.APPLICATION_STATUS)
indicator.set_status(tray.IndicatorStatus.ACTIVE)
indicator.set_menu(win.create_menu())
win.connect("destroy", Gtk.main_quit)
win.item_activated(win, 1)
Gtk.main()
