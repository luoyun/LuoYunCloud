# coding: utf-8

import logging, datetime, time, re
import tornado
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from app.wiki.models import WikiCatalog, Topic
from app.wiki.forms import TopicForm, NewTopicForm


from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])



class Index(LyRequestHandler):

    def get(self):

        catalogs = self.db2.query(WikiCatalog).all()

        self.render( 'wiki/index.html', title = _('Servers Home'), catalogs = catalogs )



class ViewTopic(LyRequestHandler):

    def get(self, id):

        topic = self.db2.query(Topic).get(id)
        if not topic:
            return self.write('Have not found topic %s' % id)

        d = { 'title': _('View topic: %s') % topic.name,
              'topic': topic }

        self.render('wiki/view_topic.html', **d)



class ViewTopicSource(LyRequestHandler):

    def get(self, id):

        topic = self.db2.query(Topic).get(id)
        if not topic:
            return self.write('Have not found topic %s' % id)

        self.set_header("Content-Type", "text/plain")
        self.write(topic.body)



class NewTopic(LyRequestHandler):

    @authenticated
    def get(self):

        catalog_id = self.get_argument('catalog', 1)
        catalog = self.db2.query(WikiCatalog).get( catalog_id )
        if not catalog:
            return self.write( _('Catalog not found') )

        # TODO: permission check for this catalog

        form = NewTopicForm()
        form.catalog.data = catalog_id

        self.render( 'wiki/new_topic.html', title = _('New Topic'), form = form )


    @authenticated
    def post(self):

        form = NewTopicForm( self.request.arguments )
        if form.validate():
            topic = Topic( name = form.name.data,
                           body = form.body.data,
                           user = self.current_user,
                           catalog = form.catalog.data )

            self.db2.add(topic)
            self.db2.commit()
            url = self.reverse_url('wiki:view', topic.id)
            return self.redirect(url)

        self.render( 'wiki/new_topic.html', title = _('New Topic'), form = form )



class EditTopic(LyRequestHandler):


    @authenticated
    def prepare(self):

        _id = re.match('.*/([0-9]+)/.*', self.request.path).groups()[0]

        self.topic = self.db2.query(Topic).get(_id)
        if not self.topic:
            self.write('Have not found topic %s' % _id)
            return self.finished()

        if self.topic.user_id != self.current_user.id:
            self.write('You have not permission !')
            return self.finished()


    def get(self, id):

        form = TopicForm()
        form.name.data = self.topic.name
        form.catalog.data = self.topic.catalog
        form.body.data = self.topic.body

        title = _('Edit Topic %s') % self.topic.name
        self.render( 'wiki/edit_topic.html', title = title, form = form )


    def post(self, id):

        form = TopicForm( self.request.arguments )
        if form.validate():
            self.topic.name = form.name.data
            self.topic.body = form.body.data
            self.topic.catalog = form.catalog.data
            self.topic.body_html = YMK.convert( self.topic.body )
            self.db2.commit()
            url = self.reverse_url('wiki:view', self.topic.id)
            return self.redirect(url)

        self.render( 'wiki/edit_topic.html', title = _('Edit Topic'), form = form )



class DeleteTopic(LyRequestHandler):

    @authenticated
    def get(self, id):

        topic = self.db2.query(Topic).get(id)
        if not topic:
            return self.write('Have not found topic %s' % id)

        if self.current_user.id != topic.user_id:
            return self.write('You have not permission to edit this topic !')

        self.db2.delete(topic)
        self.db2.commit()
        self.write('Delete topic %s success !' % id)



class ViewCatalog(LyRequestHandler):


    def get(self, id):

        catalog = self.db2.query(WikiCatalog).get(id)
        if not catalog:
            return self.write(u'No such catalog !')
        
        self.render( 'wiki/view_catalog.html',
                     catalog = catalog,
                     title = u'View catalog: %s' % catalog.name )

