#!/usr/bin/env python

import sys
import xmlrpclib

rpc_srv = xmlrpclib.ServerProxy("http://athlon/xmlrpc/")
#result = rpc_srv.multiply( int(sys.argv[1]), int(sys.argv[2]))
#print "%s * %s = %s" % (sys.argv[1], sys.argv[2], result)

domain_id = int(sys.argv[1])
domain_status = sys.argv[2]
result = rpc_srv.update_domain_status( domain_id, domain_status )
print "result = ", result
