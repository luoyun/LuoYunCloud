import logging

from lycustom import RequestHandler, has_permission

from app.network.models import NetworkPool, IPPool, \
    Gateway, PortMapping

from .forms import GatewayForm

from ytool.pagination import pagination
from sqlalchemy import and_, asc, desc


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



