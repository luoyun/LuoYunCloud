# LYWEB configure
IMAGE_ROOT_URL = 'http://corei5/images/'
LY_IMAGE_PATH = '/opt/LuoYun/images/'
LY_IMAGE_UPLOAD_PATH = '/opt/LuoYun/upload/'
#LY_IMAGE_UPLOAD_PATH = '/var/lib/libvirt/images/'

LY_NODE_DEFAULT_PORT = 3260

LY_CLC_DAEMON_HOST = '192.168.1.11'
LY_CLC_DAEMON_PORT = 1369


import socket

class Daemon:

    def __init__(self, host = None, port = None):

        self.host = host if host else LY_CLC_DAEMON_HOST
        self.port = port if port else LY_CLC_DAEMON_PORT

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect( (self.host, self.port) )

    def sendall(self, data):
        self.connect()
        self.socket.sendall(data)
        self.close()

    def close(self):
        self.socket.close()


LY_CLC_DAEMON = Daemon()


LYWEB_DOMAIN_LIFECYCLE_FLAG = {
    'run' : 1,
    'shutdown' : 2,
    }

LYWEB_DOMAIN_CONTROL_FLAG = {
    'run' : 1,
    'shutdown' : 2,
    'reboot' : 3,
    'start' : 4,
    'update': 10,
    }

LYCMD_TYPE = {
    'LYCMD_DOMAIN_LIFECYCLE_CONTROL': 1,
    'LYCMD_DOMAIN_STATUS_UPDATE': 2,
    'LYCMD_DOMAIN_CONTROL': 3,
    'LYCMD_NODE_CONTROL': 4,
}


LYWEB_NODE_CONTROL_FLAG = {
    'run' : 1,
    'shutdown' : 2,
    'reboot' : 3,
    'start' : 4,
    'update': 10,
    }

LYWEB_JOB_STATUS = {
    'unknown': 0,
    'prepare': 1,
    'running': 2,
    'finished': 3,
    'failed': 4,
    'stoped': 5,
    'pending': 10,
}

LYWEB_JOB_ACTION = {
    'unknown': 0,
    'run': 1,
    'stop': 2,
    'suspend': 3,
    'save': 4,
    'reboot': 5,
}

LYWEB_JOB_TARGET_TYPE = {
    'unknown': 0,
    'node': 1,
    'domain': 2,
}


# LuoYun socket target
LST_WEB_S = 1
LST_CONTROL_S = 2
LST_COMPUTE_S = 3

# LuoYun socket action
LA_WEB_NEW_JOB = 11


