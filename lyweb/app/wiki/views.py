# coding: utf-8

import logging, datetime, time, re
import tornado
from lycustom import RequestHandler
from tornado.web import authenticated, asynchronous

from app.wiki.models import WikiCatalog, Topic
from app.wiki.forms import TopicForm, NewTopicForm

from lycustom import has_permission

from sqlalchemy.sql.expression import asc, desc

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])


class Index(RequestHandler):

    def get(self):

        catalogs = self.db.query(WikiCatalog).order_by(
            asc(WikiCatalog.position)).all()

        self.render( 'wiki/index.html', title = self.trans(_('FAQ Home')), catalogs = catalogs )



class ViewTopic(RequestHandler):

    def get(self, id):

        topic = self.db.query(Topic).get(id)
        if not topic:
            return self.write('Have not found topic %s' % id)

        d = { 'title': self.trans(_('View topic: %s')) % topic.name,
              'topic': topic }

        self.render('wiki/view_topic.html', **d)



class ViewTopicSource(RequestHandler):

    def get(self, id):

        topic = self.db.query(Topic).get(id)
        if not topic:
            return self.write('Have not found topic %s' % id)

        self.set_header("Content-Type", "text/plain")
        self.write(topic.body)



class NewTopic(RequestHandler):

    @has_permission('admin')
    def get(self):

        catalog_id = self.get_argument('catalog', 1)
        catalog = self.db.query(WikiCatalog).get( catalog_id )
        if not catalog:
            return self.write( self.trans(_('Catalog not found')) )

        # TODO: permission check for this catalog

        form = NewTopicForm(self)
        form.catalog.data = catalog_id

        self.render( 'wiki/new_topic.html', title = self.trans(_('New Topic')), form = form )


    @has_permission('admin')
    def post(self):

        form = NewTopicForm(self)
        if form.validate():
            topic = Topic( name = form.name.data,
                           body = form.body.data,
                           user = self.current_user,
                           catalog = form.catalog.data )

            self.db.add(topic)
            self.db.commit()
            url = self.reverse_url('wiki:view', topic.id)
            return self.redirect(url)

        self.render( 'wiki/new_topic.html', title = self.trans(_('New Topic')), form = form )



class EditTopic(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        _id = re.match('.*/([0-9]+)/.*', self.request.path).groups()[0]

        self.topic = self.db.query(Topic).get(_id)
        if not self.topic:
            self.write('Have not found topic %s' % _id)
            return self.finish()

        if not ( self.topic.user_id == self.current_user.id or
                 self.has_permission('admin') ):
            self.write('No permission!')
            return self.finish()


    def get(self, id):

        form = TopicForm(self)
        form.name.data = self.topic.name
        form.catalog.data = self.topic.catalog
        form.body.data = self.topic.body

        title = self.trans(_('Edit Topic %s')) % self.topic.name
        self.render( 'wiki/edit_topic.html', title = title, form = form )


    def post(self, id):

        form = TopicForm(self)
        if form.validate():
            self.topic.name = form.name.data
            self.topic.body = form.body.data
            self.topic.catalog = form.catalog.data
            self.topic.body_html = YMK.convert( self.topic.body )
            self.db.commit()
            url = self.reverse_url('wiki:view', self.topic.id)
            return self.redirect(url)

        self.render( 'wiki/edit_topic.html', title = self.trans(_('Edit Topic')), form = form )



class DeleteTopic(RequestHandler):

    @has_permission('admin')
    def get(self, id):

        topic = self.db.query(Topic).get(id)
        if not topic:
            return self.write('Have not found topic %s' % id)

        self.db.delete(topic)
        self.db.commit()
        self.write('Delete topic %s success !' % id)



class ViewCatalog(RequestHandler):


    def get(self, id):

        catalog = self.db.query(WikiCatalog).get(id)
        if not catalog:
            return self.write(u'No such catalog !')
        
        self.render( 'wiki/view_catalog.html',
                     catalog = catalog,
                     title = u'View catalog: %s' % catalog.name )

