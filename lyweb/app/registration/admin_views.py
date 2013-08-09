# coding: utf-8

from ..auth.models import User
from ..site.models import SiteConfig, SiteLocaleConfig

from sqlalchemy import and_

from lycustom import RequestHandler, has_permission


class Index(RequestHandler):

    ''' Show all config about registration '''

    title = _('Site Registration Config')
    template_path = 'admin/registration/index.html'

    @has_permission('admin')
    def get(self):

        d = {
            'registration_status': SiteConfig.get(
                self.db, 'registration.status'),

            'registration_host': SiteConfig.get(
                self.db, 'registration.host'),

            'smtp_fromaddr': SiteConfig.get(
                self.db, 'notice.smtp.fromaddr'),

            'smtp_server': SiteConfig.get(
                self.db, 'notice.smtp.server'),

            'smtp_port': SiteConfig.get(
                self.db, 'notice.smtp.port'),

            'smtp_username': SiteConfig.get(
                self.db, 'notice.smtp.username'),

            'smtp_password': SiteConfig.get(
                self.db, 'notice.smtp.password'),

            'subjects': self.db.query(SiteLocaleConfig).filter_by(
                key = 'registration.email.subject' ).all(),

            'welcomes': self.db.query(SiteLocaleConfig).filter_by(
                key = 'registration.email.welcome' ).all() }

        self.render(**d)



class RegistrationStatusToggle(RequestHandler):

    @has_permission('admin')
    def get(self):

        status = self.db.query(SiteConfig).filter_by(
            key = 'registration.status' ).first()

        if status:
            status.value = 'false' if status.value == 'true' else 'true'
        else:
            status = SiteConfig(key='registration.status', value='false')

        self.db.add(status)
        self.db.commit()

        self.redirect( self.reverse_url('admin:registration') )

