# -*- coding: utf-8 -*-

import os
import sys
import wx
from wx.lib.wordwrap import wordwrap

licenseText = "GPLv3"

class SysTrayIcon(wx.TaskBarIcon):

    ID_ABOUT = wx.NewId()
    ID_EXIT = wx.NewId()

    def __init__(self, *args, **kargs):
        super(SysTrayIcon, self).__init__(*args, **kargs)

        # setup icon object
        icon = wx.Icon('osm.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon, "LuoYunCloud OSM is running.")

        self.frame = wx.Frame(None)
        self.menu = None
        self.info = None

        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftClick)

    def GetMenu(self, evt=None):
        if not self.menu:
            self.menu = wx.Menu()
            self.menu.Append(self.ID_ABOUT, "About")
            self.menu.AppendSeparator()
            self.menu.Append(self.ID_EXIT,   "Exit")

            self.Bind(wx.EVT_MENU, self.OnAbout, id=self.ID_ABOUT)
            self.Bind(wx.EVT_MENU, self.OnExit, id=self.ID_EXIT)

        return self.menu

    def OnTaskBarLeftClick(self, evt):
        self.PopupMenu(self.GetMenu())

    def OnAbout(self, evt):
        if not self.info:
            info = wx.AboutDialogInfo()
            info.Name = "LuoYunCloud OSM"
            info.Version = "0.6"
            info.Copyright = "(C) 2011-2013 LuoYun"
            info.Description = wordwrap(
                "LuoYunCloud OSM is a agent."
                "Install in the guest OS, make a community between the guest OS and the platform. ",
                # change the wx.ClientDC to use self.panel instead of self
                350, wx.ClientDC(self.frame))
            info.WebSite = ("http://www.luoyun.co", "LuoYun Home")
            info.Developers = [ "LuoYun Dev <contact@luoyun.co>" ]

            # change the wx.ClientDC to use self.panel instead of self
            info.License = wordwrap(licenseText, 500, wx.ClientDC(self.frame))

            self.info = info

        else:
            info = self.info

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)

    def OnExit(self, evt):
        dlg = wx.MessageDialog(self.frame, "Want to exit OSM tray ?", "Exit OSM", wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            self.RemoveIcon()
            self.Destroy()
            dlg.Destroy()
            sys.exit()


def main():

    # setup app
    app = wx.PySimpleApp()

    # setup taskbar icon
    systray = SysTrayIcon()

    app.MainLoop()


if __name__ == '__main__':

    main()
