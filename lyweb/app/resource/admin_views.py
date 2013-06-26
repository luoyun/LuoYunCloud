import datetime

from lycustom import RequestHandler, has_permission

from sqlalchemy import desc, asc, and_

from .models import Resource
from .forms import ResourceForm
from .utils import resource_mail_notice

from ytool.pagination import pagination



class ResourceIndex(RequestHandler):

    @has_permission('admin')
    def get(self):

        page_size = self.get_argument_int('sepa', 50)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        order = self.get_argument_int('order', 1)
        gid = self.get_argument_int('gid', -1)

        RL = self.db.query(Resource)
        total = RL.count()

        by_obj = Resource.id
        by_exp = desc(by_obj) if order else asc(by_obj)

        RL = RL.order_by( by_exp )

        start = (cur_page - 1) * page_size
        stop = start + page_size

        RL = RL.slice(start, stop)

        page_html = pagination( self.request.uri, total,
                                page_size, cur_page )

        d = { 'title': self.trans(_('Admin User Management')),
              'RESOURCE_TOTAL': total,
              'urlupdate': self.urlupdate,
              'RESOURCE_LIST': RL, 'PAGE_HTML': page_html,
              'PAGE_SIZE': page_size }

        self.render( 'admin/resource/index.html', **d )



class ResourceView(RequestHandler):

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', 0)
        resource = self.db.query(Resource).get(ID)
        if not resource:
            return self.write( _('No such resource: %s') % ID )

        d = { 'title': _('View Resource %s') % ID,
              'resource': resource }

        self.render('admin/resource/view.html', **d)



class ResourceEdit(RequestHandler):

    title = _('Edit Resource')
    template_path = 'admin/resource/edit.html'

    @has_permission('admin')
    def prepare(self):

        ID = self.get_argument_int('id', 0)
        self.resource = self.db.query(Resource).get(ID)
        if not self.resource:
            self.write( _('No such resource: %s') % ID )
            return self.finish()

        type_choices = []
        for x, y in Resource.RESOURCE_TYPE:
            type_choices.append( (str(x), y) )

        self.form = ResourceForm(self)
        self.form.type.choices = type_choices

        self.prepare_kwargs['resource'] = self.resource
        self.prepare_kwargs['form'] = self.form

    def get(self):

        resource = self.resource
        form = self.form
        
        form.type.default = resource.type
        form.process()

        form.size.data = resource.size
        form.effect_date.data = resource.effect_date
        form.expired_date.data = resource.expired_date

        self.render( form = form, resource = resource )

    def post(self):

        resource = self.resource
        form = self.form

        if form.validate():
            resource.type = form.type.data
            resource.size = form.size.data
            resource.effect_date = form.effect_date.data
            resource.expired_date = form.expired_date.data
            self.db.add( resource )
            self.db.commit()

            resource.user.profile.update_resource_total()

            # count be choices, email notice
            resource_mail_notice(self, resource.user)

            url = self.reverse_url('admin:resource')
            return self.redirect_next( url )

        self.render( form = form, resource = resource )



class ResourceDelete(RequestHandler):

    title = _('Delete Resource')

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', 0)
        resource = self.db.query(Resource).get( ID )
        if not resource:
            return self.write( _('No such resource: %s') % resource_id )

        U = resource.user

        self.db.delete( resource )
        self.db.commit()

        resource.user.profile.update_resource_total()

        # count be choices, email notice
        resource_mail_notice(self, U)

        url = self.reverse_url('admin:resource')
        self.redirect_next( url )

