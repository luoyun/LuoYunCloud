import struct
import lydef, lylog, lyutil

LOG = lylog.logger()

def procOSMQuery(sock, datalen, data):
  l = struct.calcsize("i")
  if datalen != l or len(data) != l:
    LOG.error("wrong OSM query packet")
    return 1
  lyutil.socksend(sock, PKT_TYPE_CLC_OSM_QUERY_REPLY,
                  "%s %d %d %s" % (data, lyconf.Config.tag, lyconf.Config.status, lyconf.Config.local_ip))
  return 0

def process(sock, packet):
  h = struct.calcsize("=LL")
  type, datalen = struct.unpack("=LL", packet[:h])
  if type == PKT_TYPE_TEST_ECHO_REQUEST:
    sock.socksend(sock, PKT_TYPE_TEST_ECHO_REPLY, packet[h:])
  elif type == PKT_TYPE_CLC_OSM_QUERY_REQUEST:
    procOSMQuery(sock, datalen, packet[h:])
  else:
    LOG.error("unrecognized clc packet")
     
