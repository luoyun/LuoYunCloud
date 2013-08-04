import logging

from lycustom import RequestHandler, has_permission

from app.network.models import NetworkPool, IPPool, \
    Gateway, PortMapping

from .forms import GatewayForm, NetworkPoolForm

from ytool.pagination import pagination
from sqlalchemy import and_, asc, desc

from IPy import IP


class Index(RequestHandler):

    @has_permission('admin')
    def get(self):

        d = { 'title': _('Network Summary'),
              'networkpool_list': self.db.query(NetworkPool).all(),
              'gateway_list': self.db.query(Gateway).all(),
              'portmapping_count': self.db.query(PortMapping.id).count() }

        self.render('/admin/network/index.html', **d )


class IPPoolIndex(RequestHandler):

    @has_permission('admin')
    def get(self):

        page_size = self.get_argument_int('sepa', 50)
        cur_page = self.get_argument_int('p', 1)
        nid = self.get_argument_int('network', 0)
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')

        if by == 'created':
            by = IPPool.created
        elif by == 'network':
            by = IPPool.network_id
        else:
            by = IPPool.id

        by_exp = desc(by) if sort == 'DESC' else asc(by)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        N = self.db.query(NetworkPool).get(nid) if nid else None

        TOTAL = self.db.query(IPPool.id).count()

        POOL = self.db.query(IPPool)
        if N:
            POOL = POOL.filter( IPPool.network_id == nid )

        POOL = POOL.order_by( by_exp )
        POOL = POOL.slice(start, stop)

        page_html = pagination(self.request.uri, TOTAL, page_size, cur_page)


        d = { 'title': _('IP Pool'), 'TOTAL': TOTAL, 'NETWORK': N,
              'IPPOOL': POOL.all(), 'PAGE_HTML': page_html }

        self.render('admin/network/ippool.html', **d)



class GatewayIndex(RequestHandler):

    @has_permission('admin')
    def get(self):

        d = { 'title': _('Gateway Summary'),
              'gateway_list': self.db.query(Gateway).all() }

        self.render('/admin/network/gateway.html', **d )


class GatewayHandler(RequestHandler):

    def add_to_portmapping(self, G):

        start, end = G.start, G.end
        exclude_ports = [ int(x.strip()) 
                          for x in G.exclude_ports.split() ]

        cur = start
        while cur < end:

            if cur in exclude_ports:
                cur += 1
                continue

            if self.db.query(PortMapping).filter_by(
                gateway_port = cur ).first():
                logging.warn('ADD gateway: port %s is exists, ommit.' % cur)
            else:
                P = PortMapping( gateway_port = cur,
                                 gateway_id = G.id )
                self.db.add( P )

            cur += 1

        self.db.commit()



class GatewayConfig(GatewayHandler):

    title = _('Gateway Configure')
    template_path = 'admin/network/gateway_config.html'

    @has_permission('admin')
    def prepare(self):

        self.gateway = None

        ID = self.get_argument('gateway', None)
        if ID:
            gateway = self.db.query(Gateway).get( ID )
            if gateway:
                self.gateway = gateway

        self.prepare_kwargs['form'] = GatewayForm(self)


    def get(self):
        if self.gateway:
            G = self.gateway
            form = self.prepare_kwargs['form']

            form.name.data = G.name
            form.description.data = G.description
            form.ip.data = G.ip
            form.netmask.data = G.netmask
            form.start.data = G.start
            form.end.data = G.end
            form.exclude_ports.data = G.exclude_ports
            
        self.render()


    def post(self):

        form = self.prepare_kwargs['form']

        if form.validate():

            if self.gateway:
                G = self.gateway
                G.name = form.name.data
                G.description = form.description.data
                G.ip = form.ip.data
                G.netmask = form.netmask.data
                G.start = form.start.data
                G.end = form.end.data
                G.exclude_ports = form.exclude_ports.data

            else:
                G = Gateway(
                    name          = form.name.data,
                    description   = form.description.data,
                    ip            = form.ip.data,
                    netmask       = form.netmask.data,
                    start         = form.start.data,
                    end           = form.end.data,
                    exclude_ports = form.exclude_ports.data )

                self.db.add( G )

            self.db.commit()

            self.add_to_portmapping( G )

            url = self.reverse_url('admin:network:gateway')
            return self.redirect( url )

        self.render()



class PortMappingIndex(RequestHandler):

    @has_permission('admin')
    def get(self):

        page_size = self.get_argument_int('sepa', 50)
        cur_page = self.get_argument_int('p', 1)
        gid = self.get_argument_int('gateway', 0)
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')

        has_ip = self.get_argument('has_ip', False)

        if by == 'created':
            by = PortMapping.created
        elif by == 'network':
            by = PortMapping.gateway_id
        else:
            by = PortMapping.id

        by_exp = desc(by) if sort == 'DESC' else asc(by)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        G = self.db.query(Gateway).get(gid) if gid else None

        binding_total = self.db.query(PortMapping.id).filter(
            PortMapping.ip != None).count()

        PORT_L = self.db.query(PortMapping)
        if G:
            PORT_L = PORT_L.filter( PortMapping.gateway_id == gid )

        if has_ip:
            PORT_L = PORT_L.filter( PortMapping.ip != None )

        TOTAL = PORT_L.count()

        PORT_L = PORT_L.order_by( by_exp )
        PORT_L = PORT_L.slice(start, stop)

        page_html = pagination(self.request.uri, TOTAL, page_size, cur_page)


        d = { 'title': _('IP Pool'), 'TOTAL': TOTAL, 'gateway': G,
              'binding_total': binding_total,
              'portmapping_list': PORT_L.all(),
              'PAGE_HTML': page_html }

        self.render('admin/network/portmapping.html', **d)



class NetworkHandler(RequestHandler):

    def add_to_ippool(self, N):

        start, end = IP( N.start ), IP( N.end )
        exclude_ips = N.exclude_ips

        NETWORK = '%s/%s' % (N.start, N.netmask)
        for x in IP(NETWORK, make_net=True):
            cur_ip = IP(x)
            if cur_ip > end:
                break

            if start <= cur_ip:
                ip_str = x.strNormal()
                if not exclude_ips.count(ip_str):
                    if self.db.query(IPPool).filter_by(ip=ip_str).first():
                        logging.warning('ADD IP failed: %s is exists, ommit.' % ip_str)
                    else:
                        self.db.add( IPPool(ip_str, N) )

        self.db.commit()



class NetworkConfig(NetworkHandler):

    title = _('Network Configure')
    template_path = 'admin/network/network_config.html'

    @has_permission('admin')
    def prepare(self):

        self.network = None

        ID = self.get_argument('network', None)
        if ID:
            network = self.db.query(NetworkPool).get( ID )
            if network:
                self.network = network

        self.prepare_kwargs['form'] = NetworkPoolForm(self)


    def get(self):
        if self.network:
            N = self.network
            form = self.prepare_kwargs['form']

            form.name.data = N.name
            form.description.data = N.description
            form.start.data = N.start
            form.end.data = N.end
            form.netmask.data = N.netmask
            form.gateway.data = N.gateway
            form.nameservers.data = N.nameservers
            form.exclude_ips.data = N.exclude_ips
            
        self.render()


    def post(self):

        form = self.prepare_kwargs['form']

        if form.validate():

            if self.network:
                N             = self.network
                N.name        = form.name.data
                N.description = form.description.data
                N.start       = form.start.data
                N.end         = form.end.data
                N.netmask     = form.netmask.data
                N.gateway     = form.gateway.data
                N.nameservers = form.nameservers.data
                N.exclude_ips = form.exclude_ips.data

            else:
                N = NetworkPool(
                    name        = form.name.data,
                    description = form.description.data,
                    start       = form.start.data,
                    end         = form.end.data,
                    netmask     = form.netmask.data,
                    gateway     = form.gateway.data,
                    nameservers = form.nameservers.data,
                    exclude_ips = form.exclude_ips.data )

                self.db.add( N )

            self.db.commit()

            # TODO: can not suitable for edit now !
            self.add_to_ippool( N )

            url = self.reverse_url('admin:network')
            return self.redirect( url )

        self.render()



class NetworkDelete(NetworkHandler):

    @has_permission('admin')
    def get(self):

        ID = self.get_argument('id', None)
        if not ID:
            return self.write( _('Give me network pool id please.') )

        N = self.db.query(NetworkPool).get( ID )
        if not N:
            return self.write( _('Can not find network pool %s') % ID )

        ERROR = []

        IP_LIST = self.db.query(IPPool).filter_by( network_id = ID)

        for IP in IP_LIST:
            if IP.instance_id:
                ERROR.append( _('%s was used by instance %s') % (
                        IP.ip, IP.instance_id ) )

        if ERROR:
            d = { 'title': _('Delete NetworkPool failed'),
                  'network': N, 'ERROR': ERROR }
            return self.render('admin/network/network_delete_failed.html', **d)

        # delete ip
        for IP in IP_LIST:
            self.db.delete(IP)

        self.db.commit()

        # delete network pool
        self.db.delete( N )
        self.db.commit()
        
        url = self.reverse_url('admin:network')
        return self.redirect( url )
