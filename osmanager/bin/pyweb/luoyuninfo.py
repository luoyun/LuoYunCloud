import sys
import os
import datetime

def get_sysinfo(hostname = None):
    """Get system info, including
       $hostname $application $version1 $version2 $curtime"""
    if hostname == None or hostname == "":
        f = os.popen("/sbin/ifconfig eth0")
        s = f.read()
        if f.close() == None: 
            for l in s.split('\n'):
                l = l.strip()
                inet = l.split(':')[0]
                if inet == 'inet addr':
                    l = l.split(':')[1]
                    hostname = l.split(' ')[0]
                    break
    version1 = "unknown"
    application = "unknown"
    version2 = "unknown"
    f = None
    try:
        f = open("/LuoYun/build/VERSION")
        s = f.readlines()
        version1 = s[0].split()[1]
        application = s[1].split()[0]
        application = application.strip(':')
        version2 = s[1].split()[1]
    except os.error:
        print "Warning: reading /LuoYun/build/VERSION error\n"
    curtime = datetime.datetime.now().timetuple()
    curtime = "%02d:%02d" % (curtime[3], curtime[4])
    return dict(hostname=hostname.encode('utf-8'),
                version1=version1.encode('utf-8'),
                application=application.encode('utf-8'),
                version2=version2.encode('utf-8'),
                curtime=curtime.encode('utf-8'))

if __name__ == '__main__':
    print "retrieve sys info"
    sys.exit(0)

