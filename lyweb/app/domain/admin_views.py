import json

from lycustom import RequestHandler, has_permission

from app.site.models import SiteConfig

from .forms import DomainForm


class DomainIndex(RequestHandler):

    @has_permission('admin')
    def get(self):

        domain = self.db.query(SiteConfig).filter_by(
            key = 'domain' ).first()

        if domain:
            domain = json.loads(domain.value) if domain.value else {}

        self.render('/admin/domain/index.html', domain = domain)


class DomainEdit(RequestHandler):

    title = _('Configure Site Domain')
    template_path = 'admin/domain/edit.html'

    @has_permission('admin')
    def prepare(self):

        self.domain = self.db.query(SiteConfig).filter_by(
            key = 'domain' ).first()

        self.form = DomainForm(self)
        self.prepare_kwargs['form'] = self.form

    def get(self):

        form = self.form

        if self.domain:
            domain = json.loads(self.domain.value)
            if domain > 0:
                form.topdomain.data = domain['topdomain']
                form.prefix.data = domain['prefix']
                form.suffix.data = domain['suffix']

        self.render()


    def post(self):

        form = self.form

        if form.validate():

            domain = json.dumps( {
                    'topdomain': form.topdomain.data,
                    'prefix': form.prefix.data,
                    'suffix': form.suffix.data } )

            if self.domain:
                self.domain.value = domain
            else:
                new = SiteConfig( key = 'domain', value = domain )
                self.db.add( new )

            self.db.commit()

            url = self.reverse_url('admin:domain')
            self.redirect( url )

        self.render()



