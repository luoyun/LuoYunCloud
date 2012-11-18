import subprocess
import struct
import socket
import select
import lylog
import uuid

LOG = lylog.logger()

def socksend(sock, type, data):
  l = len(data)
  mreq = struct.pack("=LL%ds" % l, type, l, data)
  try:
    sock.send(mreq)
    return 0
  except:
    LOG.error("socksend error\n")
    return -1

def sockrecv(sock, length = 1024, timeout = 1):
  data = b''
  # first read header
  headlen = struct.calcsize("=LL")
  while True:
    try:
      ready = select.select([sock], [], [], timeout)
      if ready[0]:
        d = sock.recv(headlen-len(data))
        if len(d) == 0:
          LOG.info("0 length packet received. return.")
          return (0, None)
        data += d
        if len(data) == headlen:
          break
        LOG.warn("partial packet received %d" % len(data))
      else:
        LOG.debug("sockrecv timed out")
        return (-1, None)
    except socket.error, (v, m):
      LOG.warn("socket error(%d): %s" % (v, m))
      return (0, None)
    except select.error, (v, m):
      LOG.warn("select error(%d): %s" % (v, m))
      return (0, None)
    except:
      LOG.error("unexpected socket select error")
      return (0, None)

  # calculate the size of data to read
  type, datalen = struct.unpack("=LL", data)
  LOG.debug("%d %d" % (type, datalen))
  if datalen == 0 or length <= headlen:
    return (0, data)
  pktlen = headlen + datalen
  if pktlen > length:
    pktlen = length
  # read the complte packet
  while True:
    try:
      ready = select.select([sock], [], [], timeout)
      if ready[0]:
        d = sock.recv(pktlen - len(data))
        if len(d) == 0:
          LOG.info("0 length packet received. return.")
          return (0, data)
        data += d
        if len(data) == pktlen:
          break
        LOG.warn("partial packet received %d" % len(data))
      else:
        LOG.warn("sockrecv timed out")
        return (-1, data)
    except socket.error, (v, m):
      LOG.warn("socket error(%d): %s" % (v, m))
      return (0, None)
    except select.error, (v, m):
      LOG.warn("select error(%d): %s" % (v, m))
      return (0, None)
    except:
      LOG.error("unexpected socket select error")
      return (0, None)

  return (pktlen, data)


def myuuid():
  try:
    a = str(uuid.uuid1())
  except OSError:
    return 1
  else:
    return a

if __name__ == "__main__":
  a = myuuid()
  print a
