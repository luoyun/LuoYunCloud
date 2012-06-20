import sys, socket
import struct
import time
import lydef, lylog, lyconf, lyauth, lyutil

LY_OSM_KEEPALIVE_INTVL  = 10
LY_OSM_KEEPALIVE_PROBES = 3

LOG = lylog.logger()

def getclcparm():
  mcast_ip = lyconf.Config.clc_mcast_ip
  mcast_port = lyconf.Config.clc_mcast_port

  sock = None
  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', mcast_port))
    mreq = struct.pack("4sl", socket.inet_aton(mcast_ip), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.settimeout(15.0)
  except socket.error, (value,message):
    LOG.warn(message)
    if sock:
        sock.close()
    return 1 

  clc_ip = b''
  clc_port = b''
  start_time = time.time()
  while True:
    try:
      pkt = sock.recv(1024)
    except socket.error, (message):
      LOG.warn(message)
      sock.close()
      return 1

    LOG.info("mcast packet: %s" % pkt)
    l = struct.calcsize("=LL")
    if len(pkt) < l:
      LOG.error("unrecognized packet")
      return 1
    pkt_type, pkt_len = struct.unpack('=LL', pkt[:l])
    LOG.info("mcast packet type:%d packet length:%d" % (pkt_type, pkt_len))
    if pkt_type != lydef.PKT_TYPE_JOIN_REQUEST:
      if time.time() - start_time > 60:
        LOG.error("mcast timed out")
        sock.close()
        return 1
      continue
    join, clc_ip, clc_port = pkt[8:].split(' ')
    if join == 'join':
      break

  if clc_ip and clc_port:
    LOG.info("mcast get CLC IP:%s PORT:%s" % (clc_ip, clc_port))
    lyconf.Config.clc_port = int(clc_port)
    lyconf.Config.clc_ip = clc_ip
    sock.close()
    return 0
  else:
    LOG.error("wrong CLC mcast packet")
    return 1


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
    sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, LY_OSM_KEEPALIVE_INTVL)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, LY_OSM_KEEPALIVE_INTVL)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, LY_OSM_KEEPALIVE_PROBES)
    sock.setblocking(0)
  except socket.error, (value,message): 
    LOG.warn(message)
    if sock: 
        sock.close()
    return None 
  lyconf.Config.local_ip = sock.getsockname()[0]
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
    t, l, s = struct.unpack("=LLi", response)
    if t != lydef.PKT_TYPE_OSM_REGISTER_REPLY:
      LOG.error("wrong packet %d" % t)
      return None
    if int(s) != lydef.LY_S_REGISTERING_DONE_SUCCESS:
      LOG.error("register to clc without sucess %s" % s)
      return None
    lyconf.Config.status = lydef.OSM_STATUS_REGISTERED
    LOG.info("register to clc successfully")

    return sock
  finally:
    if lyconf.Config.status != lydef.OSM_STATUS_REGISTERED:
      sock.close()

def connclc():
  clc_ip = lyconf.Config.clc_ip
  clc_port = lyconf.Config.clc_port
  s = None
  if clc_ip and clc_port:
    s = regclc()
  if s:
    return s
  getclcparm()
  if clc_ip == lyconf.Config.clc_ip and clc_port == lyconf.Config.clc_port:
    return None
  if lyconf.Config.clc_ip and lyconf.Config.clc_port:
    s = regclc()
  if s:
    return s
  return None
  
    
if __name__ == "__main__":
  lylog.setup()
  lyconf.Config.clc_mcast_ip = '228.0.0.1'
  lyconf.Config.clc_mcast_port = 1371
  lyconf.Config.key = b'015e33a8-787d-457e-b84d-c2a101a816e0'
  lyconf.Config.tag = 10
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

