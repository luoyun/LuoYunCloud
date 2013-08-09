import sys
import subprocess
import logging
import optparse



class MyOptionParser(optparse.OptionParser):
    def error(self, msg):
        pass



def run_cmd(cmd):
    ''' return  exit_code, stdout '''

    child = subprocess.Popen( cmd.split(), stdout=subprocess.PIPE )

    ret_code = child.wait()
    ret_stdout = child.stdout

    if ret_code != 0:
        logging.error('exec %(cmd)s failed: %(stdout)s' % {
                'cmd': cmd, 'stdout': ret_stdout })

    return ret_code, ret_stdout
    


class Prerouting(object):

    def __init__(self):
        self.parser = self.get_parser()
        self.rules = self.get_rules()

    def get_rules(self):

        rules = []
        parser = self.parser

        cmd = 'iptables -t nat -S PREROUTING'
        ret_code, ret_stdout = run_cmd( cmd )

        if ret_code == 0:

            for line in ret_stdout:
                line = line.strip('\n')

                L = line.split()

                args, opts = parser.parse_args( L )
                if args.A:
                    rules.append( args )


        return rules


    def get_parser(self):

        ''' Example:

        -A PREROUTING -d 59.37.21.199/32 -p tcp -m tcp \
        --dport 25903 -j DNAT --to-destination 10.0.0.1:5902
        '''

        parser = MyOptionParser()
        parser.add_option('-A', dest='A')
        parser.add_option('-d', dest='d', type='string')
        parser.add_option('-p', dest='p', type='string')
        parser.add_option('-m', dest='m', type='string')
        parser.add_option('-j', dest='j', type='string')
        parser.add_option('--dport', dest='dport', type='int')
        parser.add_option('--to-destination', dest='destination', type='string')

        return parser

    def delete_by_destination(self, ip, port):

        destination = '%s:%s' % (ip, port)

        for index, r in enumerate(self.rules):

            if r.destination == destination:

                # TODO: rules was changed
                if self.delete( index + 1 ):
                    logging.info('delete prerouting to %s success.' % destination)
                else:
                    logging.info('delete prerouting to %s failed.' % destination)

                return

        logging.warn('can not delete: no prerouting to %s.' % destination)

        
    def delete(self, index):


        cmd = 'iptables -t nat -D PREROUTING %s' % index
        ret_code, ret_stdout = run_cmd( cmd )

        if ret_code == 0:
            # TODO: important , rules was changed
            self.rules = self.get_rules()



    def add(self, external_ip, external_port, inner_ip, inner_port, _type='tcp'):

        '''
        iptables -t nat -I PREROUTING -d 59.37.21.199/32 -p tcp -m tcp \
        --dport 15903 -j DNAT --to-destination 10.0.0.1:5902
        '''

        if self.exists(inner_ip, inner_port):
            logging.warn('%s:%s exists, quit now.' % (inner_ip, inner_port))
            return

        cmd = 'iptables -t nat -I PREROUTING -d %(external_ip)s \
-p %(type)s -m %(type)s --dport %(external_port)s -j DNAT \
--to-destination %(inner_ip)s:%(inner_port)s' % {
            'external_ip': external_ip,
            'external_port': external_port,
            'type': _type,
            'inner_ip': inner_ip,
            'inner_port': inner_port,
            }

        ret_code, ret_stdout = run_cmd( cmd )

        if ret_code == 0:
            # TODO: important , rules was changed
            self.rules = self.get_rules()


    def list(self):

#        print '%3s | %18s : %-6s  |  %15s : %-6s' %('Num', 'External IP', 'Port', 'Inner IP', 'Port')
#        print '-' * 62

        for i, r in enumerate(self.rules):
            dst_ip, dst_port = r.destination.split(':')
            print '%3s : %18s:%-6s -> %15s:%-6s' %(i+1, r.d, r.dport, dst_ip, dst_port)

    def exists(self, ip, port):

        destination = '%s:%s' % (ip, port)

        for index, r in enumerate(self.rules):

            if r.destination == destination:
                return True

        return False


def usage():

    print '''
Usage: %s ACTION [ARGS]

ACTION  add/delete/list

ARGS:

        add ExternalIP:PORT InnerIP:PORT

            e.g.  add 59.37.21.199/32:15200 10.0.1.68:22

        delete IP:PORT

            e.g.  delete 10.0.1.68:22

        list

''' % sys.argv[0]


def main():

    if len(sys.argv) < 2:
        return usage()

    action = sys.argv[1]

    if action in ['add', 'delete', 'list']:

        prerouting = Prerouting()

        if action == 'add':
            args = sys.argv[2:]
            if len(args) != 2:
                return usage()

            external_ip, external_port = args[0].split(':')
            inner_ip, inner_port = args[1].split(':')

            prerouting.add(external_ip, external_port, inner_ip, inner_port)


        elif action == 'delete':
            args = sys.argv[2:]
            if len(args) != 1:
                return usage()

            ip, port = args[0].split(':')
            prerouting.delete_by_destination(ip, port)

        elif action == 'list':
            prerouting.list()

    else:
        usage()



if __name__ == '__main__':

    main()
