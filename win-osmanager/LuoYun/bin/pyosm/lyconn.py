import sys, socket
import struct
import time
import lydef, lylog, lyconf, lyauth, lyutil

LY_OSM_KEEPALIVE_INTVL  = 10
LY_OSM_KEEPALIVE_PROBES = 3

LOG = lylog.logger()

def regclc():
  clc_ip = lyconf.Config.clc_ip
  clc_port = lyconf.Config.clc_port
  tag = lyconf.Config.tag
  mykey = lyconf.Config.key
  myuuid = lyutil.myuuid()
  if myuuid == 1:
    LOG.error("failed generating uuid")
    return None
  LOG.info("osm challenge myuuid: %s" % myuuid)
  for i in range(len(myuuid), lydef.LUOYUN_AUTH_DATA_LEN):
    myuuid += '\x00'

  data = []
  for m in myuuid:
    data.append(ord(m))
  challenge = lyauth.encode(mykey, data)
  challengestr = b''
  for m in challenge:
    challengestr += chr(m)

  LOG.info("connecting %s:%d" % (clc_ip, clc_port))
  sock = None
  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((clc_ip, clc_port))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    #sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, LY_OSM_KEEPALIVE_INTVL)
    #sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, LY_OSM_KEEPALIVE_INTVL)
    #sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, LY_OSM_KEEPALIVE_PROBES)
    sock.setblocking(0)
  except socket.error, (value,message): 
    LOG.warn(message)
    if sock: 
        sock.close()
    return None 
  lyconf.Config.local_ip=socket.gethostbyname(socket.gethostname())
  if not lyconf.Config.local_ip:
    lyconf.Config.local_ip = b'empty'

  try:
    LOG.info("send auth request %d" % tag)
    data = struct.pack("i%ds" % lydef.LUOYUN_AUTH_DATA_LEN, tag, challengestr)
    lyutil.socksend(sock, lydef.PKT_TYPE_OSM_AUTH_REQUEST, data)

    LOG.info("recv auth reply")
    recvsize = struct.calcsize("=LLi%ds" % lydef.LUOYUN_AUTH_DATA_LEN);
    result, response = lyutil.sockrecv(sock)
    if result == -1 or len(response) != recvsize:
      LOG.error("error in sockrecv")
      return None 
    if result == 0:
      LOG.error("socket closed")
      return None
    t, l, rettag, answer = struct.unpack("=LLi%ds" % lydef.LUOYUN_AUTH_DATA_LEN, response)
    if t != lydef.PKT_TYPE_OSM_AUTH_REPLY:
      LOG.error("wrong auth reply %d" % t)
      return None
    if rettag != tag:
      LOG.error("wrong auth reply %d %d %d" % (t,l,rettag))
      return None
    LOG.info("auth reply: %s" % answer)
    if answer != myuuid:
      LOG.error("wrong auth reply")
      return None
    LOG.info("CLC verified")

    LOG.info("process auth request")
    recvsize = struct.calcsize("=LLi%ds" % lydef.LUOYUN_AUTH_DATA_LEN);
    result, response = lyutil.sockrecv(sock)
    if result == -1 or len(response) != recvsize:
      LOG.error("error in sockrecv")
      return None
    if result == 0:
      LOG.error("socket closed")
      return None
    t, l, rettag, challenge = struct.unpack("=LLi%ds" % lydef.LUOYUN_AUTH_DATA_LEN, response)
    if t != lydef.PKT_TYPE_OSM_AUTH_REQUEST:
      LOG.error("wrong packet %d" % t)
      return None
    LOG.info("auth request: %s" % challenge)

    data = []
    for m in challenge:
      data.append(ord(m))
    answer = lyauth.encode(mykey, data)
    answerstr = b''
    for m in answer:
      answerstr += chr(m)
    data = struct.pack("i%ds" % lydef.LUOYUN_AUTH_DATA_LEN, tag, answerstr)
    lyutil.socksend(sock, lydef.PKT_TYPE_OSM_AUTH_REPLY, data)

    LOG.info("register to clc")
    regstr = str(tag) + ' ' + str(lydef.OSM_STATUS_UNREGISTERED) + ' ' + lyconf.Config.local_ip
    lyutil.socksend(sock, lydef.PKT_TYPE_OSM_REGISTER_REQUEST, regstr)

    LOG.info("waiting for clc reply")
    result, response = lyutil.sockrecv(sock)
    if result == -1:
      LOG.error("error in sockrecv")
      return None
    if result == 0:
      LOG.error("socket closed")
      return None
    t, l, s = struct.unpack("=LLi", response)
    if t != lydef.PKT_TYPE_OSM_REGISTER_REPLY:
      LOG.error("wrong packet %d" % t)
      return None
    if int(s) != lydef.LY_S_REGISTERING_DONE_SUCCESS:
      LOG.error("register to clc without sucess %s" % s)
      return None
    lyconf.Config.status = lydef.OSM_STATUS_REGISTERED
    LOG.info("register to clc successfully")
  finally:
    if lyconf.Config.status != lydef.OSM_STATUS_REGISTERED:
      sock.close()
      return None
    return sock

def connclc():
  clc_ip = lyconf.Config.clc_ip
  clc_port = lyconf.Config.clc_port
  s = None
  if clc_ip and clc_port:
    s = regclc()
  if s:
    return s
  return None
  
    
if __name__ == "__main__":
  lylog.setup()

  lyconf.Config.clc_ip = '192.168.1.11'
  lyconf.Config.clc_port = 13691
  lyconf.Config.status = 2
  s = connclc()
  if not s:
    LOG.error("regclc failed")
  while s:
    result, response = lyutil.sockrecv(s)
    if result <= 0:
      LOG.info("close socket")
      s.close()
      break
    print response

