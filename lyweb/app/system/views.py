# coding: utf-8

import logging, struct, socket, re, os, json
import ConfigParser

from lycustom import RequestHandler, has_permission
from tornado.web import authenticated, asynchronous

from sqlalchemy.sql.expression import asc, desc

from app.site.models import SiteConfig
from app.system.models import LuoYunConfig, LyTrace
from app.system.forms import BaseinfoForm, DBForm, \
    CLCForm, NameserversForm, \
    NginxForm, RegistrationProtocolForm, WelcomeNewUserForm, \
    QQAuth2Form

from app.auth.models import User, Group

from yweb.utils.ini import OpenINI
from yweb.utils.pagination import pagination

from email.Utils import parseaddr, formataddr
#from yweb.utils.mail import LyMail, validate_email

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])

from IPy import IP
import settings



class Index(RequestHandler):

    @has_permission('admin')
    def get(self):
        self.render('admin/system/index.html')



class DBEdit(RequestHandler):

    @has_permission('admin')
    def prepare(self):
        self.cf = OpenINI(settings.sitecfg, 'db')

    def get(self):

        cf = self.cf

        form = DBForm(self)
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

        form = DBForm(self)
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



class CLCEdit(RequestHandler):

    @has_permission('admin')
    def prepare(self):
        self.cf = OpenINI(settings.sitecfg, 'clc')

    def get(self):

        cf = self.cf

        form = CLCForm(self)
        try:
            form.ip.data = cf.get('clc_ip')
            form.port.data = cf.get('clc_port')
        except:
            pass

        self.render('system/clc_edit.html', form=form)


    def post(self):

        cf = self.cf
        saved = None

        form = CLCForm(self)
        if form.validate():
            cf.set('clc_ip', form.ip.data)
            cf.set('clc_port', form.port.data)
            cf.save()
            saved = True

        self.render('system/clc_edit.html', form=form, saved = saved)



class BaseinfoEdit(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.cf = OpenINI(settings.sitecfg, 'base')

    def get(self):

        cf = self.cf

        form = BaseinfoForm(self)
        form.app_dir.data = cf.get('appliance_top_dir', settings.appliance_top_dir)
        form.app_url.data = cf.get('appliance_top_url', settings.appliance_top_url)
        form.admin_email.data = cf.get('admin_email', settings.ADMIN_EMAIL)

        self.render('system/baseinfo_edit.html', form=form)


    def post(self):

        cf = self.cf
        saved = None

        form = BaseinfoForm(self)
        if form.validate():

            cf.set('appliance_top_dir', form.app_dir.data)
            cf.set('appliance_top_url', form.app_url.data)
            cf.set('admin_email', form.admin_email.data)
            cf.save()
            saved = True

        self.render('system/baseinfo_edit.html', form=form, saved=saved)




class NameserversEdit(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.nameservers = self.db.query(LuoYunConfig).filter_by( key = 'nameservers' ).first()


    def get(self):

        form = NameserversForm(self)
        if self.nameservers:
            form.nameservers.data = self.nameservers.value

        self.render('system/nameservers_edit.html',
                    form = form)



    def post(self):

        saved = None
        form = NameserversForm(self)
        if form.validate():

            nameservers = form.nameservers.data

            if self.nameservers:
                self.nameservers.value = nameservers
            else:
                c = LuoYunConfig('nameservers', nameservers)
                self.db.add( c )

            self.db.commit()
            saved = True

        self.render('system/nameservers_edit.html',
                    form = form, saved = saved)


class NginxEdit(RequestHandler):

    title = _('Nginx Config')
    template_path = 'system/nginx_edit.html'

    @has_permission('admin')
    def prepare(self):

        self.N = None
        self.NC = settings.NGINX_CONF

        self.N = self.db.query(SiteConfig).filter_by(
            key = 'nginx' ).first()

        if self.N and self.N.value:

            self.NC.update( json.loads( self.N.value ) )

        self.form = NginxForm(self)
        self.prepare_kwargs['form'] = self.form

        self.prepare_kwargs['saved'] = False


    def get(self):

        NC = self.NC
        form = self.form

        form.conf_path.data = NC.get('conf_path', '')
        form.log_path.data  = NC.get('log_path' , '')
        form.nginx.data     = NC.get('nginx'    , '')
        form.template.data  = NC.get('template' , '')

        self.render()


    def post(self):

        form = self.form

        if form.validate():

            nc = { 'conf_path': form.conf_path.data,
                   'log_path' : form.log_path.data,
                   'nginx'    : form.nginx.data,
                   'template' : form.template.data }

            v = json.dumps( nc )

            if self.N:
                self.N.value = v
            else:
                c = SiteConfig( 'nginx', v )
                self.db.add(c)

            self.db.commit()
            self.prepare_kwargs['saved'] = True

        self.render()



from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])
class RegistrationProtocolEdit(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.protocol = self.db.query(LuoYunConfig).filter_by(key='protocol').first()

    def get(self):

        form = RegistrationProtocolForm(self)

        # TODO: needed give a default protocol ?
        if self.protocol:
            protocol = json.loads(self.protocol.value)
            form.text.data = protocol.get('text')

        self.render('system/registration_protocol_edit.html', form = form)


    def post(self):

        saved = None
        form = RegistrationProtocolForm(self)
        if form.validate():

            protocol = json.dumps({
                    'text': form.text.data,
                    'html': YMK.convert(form.text.data) })

            if self.protocol:
                self.protocol.value = protocol
            else:
                c = LuoYunConfig('protocol', protocol)
                self.db.add(c)

            self.db.commit()
            saved = True

        self.render('system/registration_protocol_edit.html', form = form, saved = saved)



class WelcomeNewUserEdit(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.welcome = self.db.query(LuoYunConfig).filter_by(key='welcome_new_user').first()

    def get(self):

        form = WelcomeNewUserForm(self)

        # TODO: needed give a default welcome info ?
        if self.welcome:
            welcome = json.loads(self.welcome.value)
            form.text.data = welcome.get('text')

        self.render('system/welcome_new_user_edit.html', form = form)


    def post(self):

        saved = None
        form = WelcomeNewUserForm(self)
        if form.validate():

            welcome = json.dumps({
                    'text': form.text.data,
                    'html': YMK.convert(form.text.data) })

            if self.welcome:
                self.welcome.value = welcome
            else:
                c = LuoYunConfig('welcome_new_user', welcome)
                self.db.add(c)

            self.db.commit()
            saved = True

        self.render('system/welcome_new_user_edit.html', form = form, saved = saved)



class LyTraceManage(RequestHandler):


    @has_permission('admin')
    def prepare(self):

        trace_id = self.get_argument('id', 0)
        if trace_id:
            T = self.db.query(LyTrace).get( trace_id )

            if T:
                self.get_view(T)
            else:
                self.write( self.trans(_('Can not find trace %s')) % trace_id )


        else: # GET index
            self.get_index()

        # The End
        #return self.finish()


    def get_index(self):

        page_size = self.get_argument_int('sepa', 50)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        order = self.get_argument_int('order', 1)
        user_id = self.get_argument_int('user', 0)
        target_type = self.get_argument_int('target_type', None)
        target_id = self.get_argument_int('target_id', 0)
        comefrom = self.get_argument('comefrom', None)
        result = self.get_argument('result', False)

        if by in ['id', 'who_id', 'comefrom', 'target_type', 'target_id', 'isok']:
            by = by
        elif by == 'when':
            by = LyTrace.when
        elif by == 'do':
            by = LyTrace.do
        else:
            return self.write( self.trans(_('Wrong sort by value: %s')) % by )

        by_exp = desc(by) if order else asc(by)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        traces = self.db.query(LyTrace)

        if user_id:
            user = self.db.query(User).get(user_id)
            if user:
                traces = traces.filter_by(who_id=user_id)
            else:
                return self.write( self.trans(_('Can not find user by id %s')) % user_id )
        else: user = None

        traces = traces.order_by(by_exp).slice(start, stop).all()

        total = self.db.query(LyTrace.id).count()
            
        page_html = pagination(self.request.uri, total, page_size, cur_page)


        def sort_by(by):
            return self.urlupdate(
                {'by': by, 'order': 1 if order == 0 else 0, 'p': 1})

        d = { 'title': self.trans(_('Trace system action')),
              'sort_by': sort_by,
              'TRACE_LIST': traces, 'PAGE_HTML': page_html,
              'USER': user, 'TOTAL_TRACE': total }

        self.render( 'system/traces.html', **d )



    def get_view(self):
        catalogs = self.db.query(ApplianceCatalog).all()
        self.render( 'admin/appliance/view.html',
                     title = self.trans(_('View Appliance %s')) % self.appliance.name,
                     CATALOG_LIST = catalogs,
                     APPLIANCE = self.appliance,
                     human_size = human_size )



class QQAuth2Edit(RequestHandler):

    title = _('Configure Auth2 For QQ Login')
    template_path = 'system/qqauth2_edit.html'

    @has_permission('admin')
    def prepare(self):

        self.Q = self.db.query(SiteConfig).filter_by(
            key = 'qq.auth2').first()

        self.QV = json.loads( self.Q.value ) if self.Q else {}

        self.form = QQAuth2Form(self)
        self.prepare_kwargs['form'] = self.form
        self.prepare_kwargs['saved'] = False

    def get(self):

        QV = self.QV
        form = self.form

        if QV:
            form.app_id.data = QV.get('app_id', '')
            form.app_key.data = QV.get('app_key', '')
            form.redirect_uri.data = QV.get('redirect_uri', '')
            form.enabled.data = QV.get('enabled', False)

        self.render()


    def post(self):

        Q = self.Q
        form = self.form

        if form.validate():

            v = json.dumps( { 'app_id': form.app_id.data,
                              'app_key': form.app_key.data,
                              'redirect_uri': form.redirect_uri.data,
                              'enabled': form.enabled.data } )

            if Q:
                Q.value = v
            else:
                Q = SiteConfig('qq.auth2', v)

            self.db.add(Q)
            self.db.commit()

            self.prepare_kwargs['saved'] = True

        self.render()

