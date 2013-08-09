from tornado.web import authenticated
from lycustom import RequestHandler

from sqlalchemy import asc, desc, and_

from app.appliance.models import Appliance, ApplianceCatalog

from ytool.pagination import pagination

from .forms import ApplianceBaseinfoForm


class Index(RequestHandler):

    @authenticated
    def get(self):

        page_size = self.get_argument_int('sepa', 10)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        apps = self.db.query(Appliance).filter_by(
            user_id=self.current_user.id).order_by(by_exp)

        total = apps.count()
        apps = apps.slice(start, stop)
            
        page_html = pagination(self.request.uri, total, page_size, cur_page)


        d = { 'title': self.trans(_('My Appliances')),
              'APPLIANCE_LIST': apps, 'page_html': page_html }

        self.render( 'myun/appliance/index.html', **d)



class ApplianceHandler(RequestHandler):

    def initialize(self):

        self.A = None

        ID = self.get_argument_int('id', 0)
        if not ID:
            return self.write( _('Give the appliance id please.') )
        
        A = self.db.query(Appliance).get(ID)

        if A:
            if self.current_user.id != A.user_id:
                return self.write( _("Not your appliance") )
        else:
            return self.write( _('No such appliance: %s') % ID )

        self.prepare_kwargs['appliance'] = A
        self.A = A



class View(ApplianceHandler):

    @authenticated
    def get(self):

        self.render('myun/appliance/view.html')



class BaseinfoEdit(ApplianceHandler):

    title = _('Edit Base Information For Appliance')
    template_path = 'myun/appliance/baseinfo_edit.html'

    @authenticated
    def prepare(self):

        if not self.A:
            return self.finish()

        catalog_choices = []
        for s in self.db.query(ApplianceCatalog.id,
                               ApplianceCatalog.name).all():
            catalog_choices.append( (str(s.id), s.name) )

        form = ApplianceBaseinfoForm(self)
        form.catalog.choices = catalog_choices

        self.prepare_kwargs['form'] = form
        self.form = form

    def get(self):

        A = self.A
        form = self.form

        form.catalog.default = A.catalog_id
        form.os.default = A.os
        form.process()

        form.name.data = A.name
        form.summary.data = A.summary
        form.description.data = A.description

        self.render()

    def post(self):

        A = self.A
        form = self.form

        if form.validate():
            A.name        = form.name.data
            A.os          = self.get_int(form.os.data)
            A.summary     = form.summary.data
            A.catalog_id  = form.catalog.data
            A.description = form.description.data

            # Save logo file
            if self.request.files:
                r = A.save_logo(self.request.files['logo'])
                if r:
                    form.logo.errors.append( r )

            self.db.commit()
            url = self.reverse_url('myun:appliance:view')
            url += '?id=%s' % A.id
            return self.redirect( url )


        self.render()
