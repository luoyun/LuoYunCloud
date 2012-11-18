

SIZE = 256
SBox = []
i = 0
j = 0
def generateKey(mykey):
  global i, j, SBox
  keylen = len(mykey)
  SBox = []
  KBox = []
  for i in range(0, SIZE):
    SBox.append(i)
  for i in range(0, SIZE):
    KBox.append(ord(mykey[i%keylen]))
  j = 0
  for i in range(0, SIZE):
    j=(j+SBox[i]+KBox[i]) % SIZE
    tmp=SBox[i]
    SBox[i]=SBox[j]
    SBox[j]=tmp

def getByte():
  global i, j, SBox
  i=(i+1)%SIZE
  j=(j+SBox[i])%SIZE
  tmp=SBox[i]
  SBox[i]=SBox[j]
  SBox[j]=tmp

  return SBox[(SBox[i]+SBox[j])%SIZE]

def encode(mykey, data):
  generateKey(mykey)
  global i, j, SBox
  i = 0
  j = 0
  retval = []
  for m in range(0, len(data)):
    g = getByte()
    #retval.append(ord(data[m]) ^ g)
    retval.append(data[m] ^ g)
  return retval


if __name__ == "__main__":
  mykey = '015e33a8-787d-457e-b84d-c2a101a816e0'
  myuuid = '30d8e15f-0db1-43c3-9bee-4e2eb85ff6c5\x00\x00\x00'
  data = []
  for m in myuuid:
    data.append(ord(m))

  a = encode(mykey, data)
  for m in a:
    print "%x " % m
  b = encode(mykey, a)
  print b
  retstr = b''
  for m in b:
    print "%c " % m
    retstr = retstr + chr(m)
  if myuuid == retstr:
    print "passed"

