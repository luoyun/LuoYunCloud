import subprocess
import struct
import select
import lylog


LOG = lylog.logger()

def socksend(sock, type, data):
  l = len(data)
  mreq = struct.pack("=LL%ds" % l, type, l, data)
  sock.send(mreq)

def sockrecv(sock, length = 1024, timeout = 1):
  data = b''
  # first read header
  headlen = struct.calcsize("=LL")
  while True:
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
  return (pktlen, data)


def myuuid():
  cmd = 'uuidgen'
  try:
    #a = subprocess.check_output(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    a = p.stdout.readlines()[0]
  except OSError:
    return 1
  else:
    return a[:-1]

if __name__ == "__main__":
  a = myuuid()
  print a
