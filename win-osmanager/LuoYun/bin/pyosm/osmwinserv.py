# -*- coding:utf-8 -*-
# Install Service : win32_service.py install
# Remove Service  : win32_service.py remove

import win32serviceutil
import win32service
import win32api
import win32process
import servicemanager

import sys
import threading

class SysTrayTask(threading.Thread):
      
    def run(self):  
        import systray
        systray.main()

class OsmTask(threading.Thread):

    def run(self):
        import lyosm
        lyosm.main()


class LyOsmService(win32serviceutil.ServiceFramework):

    _svc_name_ = "LyOsmService"
    _svc_display_name_ = "LuoYun OSM Service"
    _svc_description_ = "A agent for LuoYunCloud"
         
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.systray_task = None
        self.osm_task = None

    def SvcStop(self):
        # Before we do anything, tell the SCM we are starting the stop process.
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # TODO: how to terminate thread friendly ?

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, ''))

        self.osm_task = OsmTask()
        self.osm_task.start()

        self.systray_task = SysTrayTask()
        self.systray_task.start()

        try:
            self.systray_task.join()
            self.osm_task.join()
            sys.exit(0)
        except SystemExit:
            pass


if __name__=='__main__':
    win32serviceutil.HandleCommandLine(LyOsmService)
