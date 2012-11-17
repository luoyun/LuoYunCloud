# coding: utf-8

import logging, struct, socket, re, os, json
import ConfigParser

from lycustom import LyRequestHandler, Pagination
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc

from app.system.models import LuoYunConfig, NetworkPool, IPPool, \
    LyTrace
from app.system.forms import BaseinfoForm, DBForm, \
    CLCForm, NameserversForm, NetworkPoolForm, DomainForm, \
    NginxForm, RegistrationProtocolForm, WelcomeNewUserForm, \
    SendMailForm

from app.account.models import User, Group

from ytool.ini import ConfigINI

from lycustom import has_permission
from email.Utils import parseaddr, formataddr
from lymail import LyMail, validate_email

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])

from IPy import IP
import settings



class Index(LyRequestHandler):

    @has_permission('admin')
    def get(self):
        self.render('system/index.html')



class DBEdit(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):
        self.cf = ConfigINI(settings.SITE_CONFIG, 'db')

    def get(self):

        cf = self.cf

        form = DBForm()
        try:
            form.dbname.data = cf.get('db_name')
            form.dbuser.data = cf.get('db_user')
            form.dbpass.data = cf.get('db_password')
            form.dbhost.data = cf.get('db_host')
            form.dbtype.data = cf.get('db_type')
        except:
            pass

        self.render('system/db_edit.html', form=form)


    def post(self):

        cf = self.cf
        saved = None

        form = DBForm( self.request.arguments )
        if form.validate():
            cf.set('db_host', form.dbhost.data)
            cf.set('db_type', form.dbtype.data)
            cf.set('db_name', form.dbname.data)
            cf.set('db_user', form.dbuser.data)
            cf.set('db_password', form.dbpass.data)
            cf.save()
            saved = True
            # TODO: Important ! db settings should check for connect !

        self.render('system/db_edit.html', form=form, saved = saved)



class CLCEdit(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):
        self.cf = ConfigINI(settings.SITE_CONFIG, 'clc')

    def get(self):

        cf = self.cf

        form = CLCForm()
        try:
            form.ip.data = cf.get('clc_ip')
            form.port.data = cf.get('clc_port')
        except:
            pass

        self.render('system/clc_edit.html', form=form)


    def post(self):

        cf = self.cf
        saved = None

        form = CLCForm( self.request.arguments )
        if form.validate():
            cf.set('clc_ip', form.ip.data)
            cf.set('clc_port', form.port.data)
            cf.save()
            saved = True

        self.render('system/clc_edit.html', form=form, saved = saved)



class BaseinfoEdit(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.cf = ConfigINI(settings.SITE_CONFIG, 'base')

    def get(self):

        cf = self.cf

        form = BaseinfoForm()
        form.app_dir.data = cf.get('appliance_top_dir', settings.appliance_top_dir)
        form.app_url.data = cf.get('appliance_top_url', settings.appliance_top_url)
        form.admin_email.data = cf.get('admin_email', settings.ADMIN_EMAIL)

        self.render('system/baseinfo_edit.html', form=form)


    def post(self):

        cf = self.cf
        saved = None

        form = BaseinfoForm( self.request.arguments )
        if form.validate():

            cf.set('appliance_top_dir', form.app_dir.data)
            cf.set('appliance_top_url', form.app_url.data)
            cf.set('admin_email', form.admin_email.data)
            cf.save()
            saved = True

        self.render('system/baseinfo_edit.html', form=form, saved=saved)




class NameserversEdit(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.nameservers = self.db2.query(LuoYunConfig).filter_by( key = 'nameservers' ).first()


    def get(self):

        form = NameserversForm()
        if self.nameservers:
            form.nameservers.data = self.nameservers.value

        self.render('system/nameservers_edit.html',
                    form = form)



    def post(self):

        saved = None
        form = NameserversForm( self.request.arguments )
        if form.validate():

            nameservers = form.nameservers.data

            if self.nameservers:
                self.nameservers.value = nameservers
            else:
                c = LuoYunConfig('nameservers', nameservers)
                self.db2.add( c )

            self.db2.commit()
            saved = True

        self.render('system/nameservers_edit.html',
                    form = form, saved = saved)


class IPPoolView(LyRequestHandler):

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

        N = self.db2.query(NetworkPool).get(nid) if nid else None

        TOTAL = self.db2.query(IPPool.id).count()

        POOL = self.db2.query(IPPool)
        if N:
            POOL = POOL.filter( IPPool.network_id == nid )

        POOL = POOL.order_by( by_exp )
        POOL = POOL.slice(start, stop)

        pagination = Pagination( total = TOTAL,
                                 page_size = page_size,
                                 cur_page = cur_page )

        page_html = pagination.html( self.get_page_url )

        d = { 'title': _('IP Pool'), 'TOTAL': TOTAL, 'NETWORK': N,
              'IPPOOL': POOL.all(), 'PAGE_HTML': page_html }

        self.render('system/ippool.html', **d)



class NetworkHome(LyRequestHandler):

    @has_permission('admin')
    def get(self):
        d = { 'title': _('Network Pool'),
              'NETWORKPOOL': self.db2.query(NetworkPool).all() }

        self.render('system/networkpool.html', **d)


class NetworkView(LyRequestHandler):

    @has_permission('admin')
    def get(self, ID):
        
        N = self.db2.query(NetworkPool).get(ID)

        if N:
            d = { 'title': _('Network Pool'), 'N': N }
            self.render('system/networkpool_view.html', **d)
        else:
            self.write( _('Can not find networkpool %s') % ID )



class NetworkHandler(LyRequestHandler):

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
                    if self.db2.query(IPPool).filter_by(ip=ip_str).first():
                        logging.warning('ADD_IPPOOL: IP %s is exists, ommit.' % ip_str)
                    else:
                        self.db2.add( IPPool(ip_str, N) )

        self.db2.commit()



class NetworkDelete(LyRequestHandler):

    @has_permission('admin')
    def get(self, ID):

        N = self.db2.query(NetworkPool).get(ID)
        if not N: return self.write( _('Can not find networkpool %s') % ID )

        ERROR = []
        OK = [] # TODO: use session rollback

        for x in self.db2.query(IPPool).filter_by(network_id=N.id):
            if x.instance:
                ERROR.append( x )
            else:
                OK.append( x )

        if ERROR:
            d = { 'title': _('Delete Network Pool Failed'),
                  'FAILED_LIST': ERROR, 'N': N }
            self.render('system/networkpool_delete_failed.html', **d)

        else:
            for x in OK:
                self.db2.delete(x)
            self.db2.delete(N)
            self.db2.commit()
            self.redirect(self.reverse_url('system:networkpool'))



class NetworkAdd(NetworkHandler):

    @has_permission('admin')
    def get(self):

        form = NetworkPoolForm()
        NS = self.db2.query(LuoYunConfig).filter_by( key = 'nameservers' ).first()
        if NS: form.nameservers.data = NS.value

        d = { 'title': _('Add a new network pool'),  'form': form }
        self.render('system/networkpool_add.html', **d)


    @has_permission('admin')
    def post(self):

        form = NetworkPoolForm( self.request.arguments )
        if form.validate():

            N = NetworkPool(
                name = form.name.data,
                description = form.description.data,
                start = form.start.data,
                end = form.end.data,
                netmask = form.netmask.data,
                gateway = form.gateway.data,
                nameservers = form.nameservers.data,
                exclude_ips = form.exclude_ips.data )

            self.db2.add( N )
            self.db2.commit()

            self.add_to_ippool(N)

            url = self.reverse_url('system:networkpool')
            return self.redirect( url )

        d = { 'title': _('Add a new network pool'),  'form': form }
        self.render('system/networkpool_add.html', **d)



class NetworkEdit(LyRequestHandler):

    @has_permission('admin')
    def get(self, ID):

        N = self.db2.query(NetworkPool).get(ID)
        if not N: return self.write( _('Can not find networkpool %s') % ID )

        form = NetworkPoolForm()
        form.name.data = N.name
        form.description.data = N.description
        form.start.data = N.start
        form.end.data = N.end
        form.netmask.data = N.netmask
        form.gateway.data = N.gateway
        if N.nameservers:
            form.nameservers.data = N.nameservers
        else:
            nameservers = self.db2.query(LuoYunConfig).filter_by( key = 'nameservers' ).first()
            if nameservers:
                form.nameservers.data = nameservers.value
        if N.exclude_ips:
            form.exclude_ips.data = N.exclude_ips

        d = { 'title': _('Edit network pool'),  'form': form }
        self.render('system/networkpool_edit.html', **d)


    def post(self, ID):

        N = self.db2.query(NetworkPool).get(ID)
        if not N: return self.write( _('Can not find networkpool %s') % ID )

        form = NetworkPoolForm( self.request.arguments )
        if form.validate():

            # TODO: a ugly algorithm
            OLD, NEW = [], []
            for x in self.db2.query(IPPool).filter_by(network_id=N.id):
                OLD.append( x.ip )

            start, end = IP( form.start.data ), IP( form.end.data )
            exclude_ips = form.exclude_ips.data

            NETWORK = '%s/%s' % (form.start.data, form.netmask.data)
            for x in IP(NETWORK, make_net=True):
                cur_ip = IP(x)
                if cur_ip > end:
                    break

                if start <= cur_ip:
                    ip_str = x.strNormal()
                    if not exclude_ips.count(ip_str):
                        NEW.append( ip_str )

            OLD_SET, NEW_SET = set(OLD), set(NEW)
            DROP = list(OLD_SET - NEW_SET)

            ERROR, OK = [], []
            for x in DROP:
                find = self.db2.query(IPPool).filter_by(ip=x).first()
                if find.instance_id:
                    ERROR.append( find )
                else:
                    OK.append( find )

            if ERROR:
                d = { 'title': _('Edit network pool failed'),
                      'UNABLE_DELETE_IP': ERROR, 'NETWORK': N,
                      'form': form }
                return self.render('system/networkpool_edit.html', **d)

            ADD = list(NEW_SET - OLD_SET)

            N.name = form.name.data
            N.description = form.name.description
            N.start = form.start.data
            N.end = form.end.data
            N.netmask = form.netmask.data
            N.gateway = form.gateway.data
            N.nameservers = form.nameservers.data
            N.exclude_ips = form.exclude_ips.data

            for x in OK:
                self.db2.delete(x)
            for x in ADD:
                self.db2.add( IPPool(x, N) )

            self.db2.commit()

            url = self.reverse_url('system:networkpool')
            return self.redirect( url )

        d = { 'title': _('Edit Network Pool'),  'form': form }
        self.render('system/networkpool_edit.html', **d)



class DomainEdit(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.domain = self.db2.query(LuoYunConfig).filter_by( key = 'domain' ).first()

    def get(self):

        form = DomainForm()
        if self.domain:
            domain = json.loads(self.domain.value)
            if domain > 0:
                form.topdomain.data = domain['topdomain']
                form.prefix.data = domain['prefix']
                form.suffix.data = domain['suffix']

        self.render('system/domain_edit.html', form = form)


    def post(self):

        saved = None
        form = DomainForm( self.request.arguments )
        if form.validate():

            domain = json.dumps( {
                    'topdomain': form.topdomain.data,
                    'prefix': form.prefix.data,
                    'suffix': form.suffix.data } )

            if self.domain:
                self.domain.value = domain
            else:
                c = LuoYunConfig('domain', domain)
                self.db2.add(c)

            self.db2.commit()
            saved = True

        self.render('system/domain_edit.html', form = form, saved = saved)



class NginxEdit(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.nginx = self.db2.query(LuoYunConfig).filter_by(key='nginx').first()

    def get(self):

        form = NginxForm()
        if self.nginx:
            nginx = json.loads(self.nginx.value)
        else:
            nginx = {}

        form.confdir.data = nginx.get(
            'conf_dir', settings.DEFAULT_NGINX_CONF_PATH )
        form.logdir.data = nginx.get(
            'log_dir', settings.DEFAULT_NGINX_LOG_PATH )
        form.binpath.data = nginx.get(
            'bin_path', settings.DEFAULT_NGINX_BIN_PATH )

        self.render('system/nginx_edit.html', form = form)


    def post(self):

        saved = None
        form = NginxForm( self.request.arguments )
        if form.validate():

            nginx = json.dumps( {
                    'conf_dir': form.confdir.data,
                    'log_dir': form.logdir.data,
                    'bin_path': form.binpath.data } )

            if self.nginx:
                self.nginx.value = nginx
            else:
                c = LuoYunConfig('nginx', nginx)
                self.db2.add(c)

            self.db2.commit()
            saved = True

        self.render('system/nginx_edit.html', form = form, saved = saved)



from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])
class RegistrationProtocolEdit(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.protocol = self.db2.query(LuoYunConfig).filter_by(key='protocol').first()

    def get(self):

        form = RegistrationProtocolForm()

        # TODO: needed give a default protocol ?
        if self.protocol:
            protocol = json.loads(self.protocol.value)
            form.text.data = protocol.get('text')

        self.render('system/registration_protocol_edit.html', form = form)


    def post(self):

        saved = None
        form = RegistrationProtocolForm( self.request.arguments )
        if form.validate():

            protocol = json.dumps({
                    'text': form.text.data,
                    'html': YMK.convert(form.text.data) })

            if self.protocol:
                self.protocol.value = protocol
            else:
                c = LuoYunConfig('protocol', protocol)
                self.db2.add(c)

            self.db2.commit()
            saved = True

        self.render('system/registration_protocol_edit.html', form = form, saved = saved)



class WelcomeNewUserEdit(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.welcome = self.db2.query(LuoYunConfig).filter_by(key='welcome_new_user').first()

    def get(self):

        form = WelcomeNewUserForm()

        # TODO: needed give a default welcome info ?
        if self.welcome:
            welcome = json.loads(self.welcome.value)
            form.text.data = welcome.get('text')

        self.render('system/welcome_new_user_edit.html', form = form)


    def post(self):

        saved = None
        form = WelcomeNewUserForm( self.request.arguments )
        if form.validate():

            welcome = json.dumps({
                    'text': form.text.data,
                    'html': YMK.convert(form.text.data) })

            if self.welcome:
                self.welcome.value = welcome
            else:
                c = LuoYunConfig('welcome_new_user', welcome)
                self.db2.add(c)

            self.db2.commit()
            saved = True

        self.render('system/welcome_new_user_edit.html', form = form, saved = saved)



class SendMail(LyRequestHandler):

    @has_permission('admin')
    def prepare(self):
        totype = self.get_argument('totype', False)
        idlist = self.get_argument('idlist', None)

        UL, GL = [], []
        if totype == 'user':
            UL = self.get_email_from_userlist( idlist )
        elif totype == 'group':
            GL = self.get_email_from_grouplist( idlist )
        elif totype == 'all':
            UL = self.db2.query(User)
        #else:
        #    return self.write( _('No totype specified !') )

        self.UL = UL
        self.GL = GL
        self.totype = totype

        self.d = { 'title': _('LuoYun Send Mail'),
                   'FROM': settings.MAIL_FROM,
                   'TOTYPE': self.totype,
                   'USER_LIST': self.UL,
                   'GROUP_LIST': self.GL }


    def get(self):

        form = SendMailForm()

        self.d['form'] = form
        self.render('system/sendmail.html', **self.d)


    def post(self):

        form = SendMailForm( self.request.arguments )
        self.d['form'] = form

        self.d['INVALID_EMAIL'] = []

        if form.validate():

            lymail = LyMail(HTML=True)

            subject = form.subject.data
            #body = YMK.convert( form.body.data )
            body = form.body.data

            CC, INVALID = self.get_email_from_text(form.cc.data)
            if len(INVALID):
                self.d['INVALID_EMAIL'].extend(INVALID)

            BCC, INVALID = self.get_email_from_text(form.bcc.data)
            if len(INVALID):
                self.d['INVALID_EMAIL'].extend(INVALID)

            # TODO: CC policy
            CC_ENABLE = True if len(self.UL) == 1 else False
            for U in self.UL:
                if CC_ENABLE:
                    lymail.sendmail(U.profile.email, subject, body, cc = CC, bcc = BCC)
                else:
                    lymail.sendmail(U.profile.email, subject, body)

            for G in self.GL:
                for U in G.users:
                    lymail.sendmail(U.profile.email, subject, body)

            TO, INVALID = self.get_email_from_text(form.to.data)
            if len(INVALID):
                self.d['INVALID_EMAIL'].extend(INVALID)

            for toaddr in TO:
                lymail.sendmail(toaddr, subject, body, cc = CC, bcc = BCC)

            lymail.close()

            form.body.data = body
            return self.render('system/sendmail_success.html', **self.d)

        self.render('system/sendmail.html', **self.d)


    def get_email_from_text(self, text):
        VALID, INVALID = [], []
        for line in text.split('\n'):
            line = line.strip().strip(',')
            for toaddr in line.split(','):
                if validate_email(toaddr):
                    VALID.append(toaddr)
                else:
                    INVALID.append(toaddr)

        return VALID, INVALID


    def get_email_from_userlist(self, to):

        if not to: return []

        L = []
        for x in to.split(','):
            try:
                x = int(x)
            except:
                continue

            u = self.db2.query(User).get(x)
            if u:
                L.append(u)
        return L

    def get_email_from_grouplist(self, to):

        if not to: return []

        L = []
        for x in to.split(','):
            try:
                x = int(x)
            except:
                continue
            g = self.db2.query(Group).get(x)
            if g:
                L.append(g)
        return L



class LyTraceManage(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        trace_id = self.get_argument('id', 0)
        if trace_id:
            T = self.db2.query(LyTrace).get( trace_id )

            if T:
                self.get_view(T)
            else:
                self.write( _('Can not find trace %s') % trace_id )


        else: # GET index
            self.get_index()

        # The End
        #return self.finish()


    def get_index(self):

        page_size = self.get_argument_int('sepa', 10)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'DESC')
        user_id = self.get_argument_int('user', 0)
        target_type = self.get_argument_int('target_type', None)
        target_id = self.get_argument_int('target_id', 0)
        comefrom = self.get_argument('comefrom', None)
        result = self.get_argument('result', False)

        if by in ['id', 'who_id', 'when', 'comefrom', 'target_type', 'isok']:
            by_exp = desc(by) if sort == 'DESC' else asc(by)
        else:
            return self.write( _('Wrong sort by value: %s') % by )

        start = (cur_page - 1) * page_size
        stop = start + page_size


        # TODO: target sort

        traces = self.db2.query(LyTrace)

        if user_id:
            user = self.db2.query(User).get(user_id)
            if user:
                traces = traces.filter_by(who_id=user_id)
            else:
                return self.write( _('Can not find user by id %s') % user_id )
        else: user = None

        traces = traces.order_by(by_exp).slice(start, stop).all()

        total = self.db2.query(LyTrace.id).count()
            
        pagination = Pagination(
            total = total,
            page_size = page_size, cur_page = cur_page )

        page_html = pagination.html( self.get_page_url )


        d = { 'title': _('Trace system action'),
              'TRACE_LIST': traces, 'PAGE_HTML': page_html,
              'USER': user, 'TOTAL_TRACE': total }

        self.render( 'system/traces.html', **d )



    def get_view(self):
        catalogs = self.db2.query(ApplianceCatalog).all()
        self.render( 'admin/appliance/view.html',
                     title = _('View Appliance %s') % self.appliance.name,
                     CATALOG_LIST = catalogs,
                     APPLIANCE = self.appliance,
                     human_size = human_size )

