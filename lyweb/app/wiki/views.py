# coding: utf-8

import logging, datetime, time, re
import tornado
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from markdown import Markdown
YMK = Markdown(extensions=['fenced_code', 'tables'])



class Index(LyRequestHandler):

    def get(self):

        limit = 10

        catalogs = self.db.query(
            'SELECT * FROM wiki_catalog;')

        for c in catalogs:

            c.topics = self.db.query(
                'SELECT * FROM topic WHERE catalog_id=%s \
LIMIT %s;',
                c.id, limit )

            for t in c.topics:

                t.user = self.db.get(
                    'SELECT * FROM auth_user WHERE id=%s;',
                    t.user_id )

        d = { 'title': 'Servers Home', 'catalogs': catalogs }

        self.render('wiki/index.html', **d)



class ViewTopic(LyRequestHandler):

    def get(self, id):

        t = self.db.get('SELECT * from topic WHERE id=%s;', id)
        if not t:
            return self.write('Have not found topic %s' % id)

        t.user = self.db.get(
            'SELECT * FROM auth_user WHERE id=%s;',
            t.user_id )

        t.catalog = self.db.get(
            'SELECT * FROM wiki_catalog WHERE id=%s;',
            t.catalog_id )

        d = { 'title': t.name, 'topic': t }

        self.render('wiki/view_topic.html', **d)



class ViewTopicSource(LyRequestHandler):

    def get(self, id):

        t = self.db.get('SELECT * from topic WHERE id=%s;', id)
        if not t:
            return self.write('Have not found topic %s' % id)

        self.set_header("Content-Type", "text/plain")
        self.write(t.body)



class NewTopic(LyRequestHandler):

    def prepare(self):
        self.d = { 'title': 'Add new topic', 'ERROR': [] }
        self.d['catalogs'] = self.db.query('SELECT * from wiki_catalog;')

    @authenticated
    def get(self):
        self.render('wiki/new_topic.html', **self.d)

    @authenticated
    def post(self):
        
        d = self.d

        d['name'] = self.get_argument('name', '').encode('utf-8')
        d['catalog'] = int(self.get_argument('catalog', 0))
        d['body'] = self.get_argument('body', '').encode('utf-8')

        if not d['name']:
            d['ERROR'].append('name can not be empty !')
        if not self.d['catalog']:
            d['ERROR'].append('no catalog selected !')
        if not self.d['body']:
            d['ERROR'].append('body can not be empty !')

        if d['ERROR']:
            return self.render('wiki/new_topic.html', **d)

        html = YMK.convert(d['body']).encode('utf-8')

        try:
            r = self.db.query(
                "INSERT INTO topic (name, body, body_html, \
catalog_id, user_id, user_ip, created, updated) VALUES \
(%s, %s, %s, %s, %s, %s, 'now', 'now') RETURNING id;",
                d['name'], d['body'], html, d['catalog'],
                self.current_user.id, self.request.remote_ip )

            return self.redirect('/wiki/topic/%s' % r[0].id)

        except Exception, emsg:
            return self.write('DB failed: %s' % emsg)


class EditTopic(LyRequestHandler):


    @authenticated
    def prepare(self):

        id = re.match('.*/([0-9]+)/.*', self.request.path).groups()[0]

        t = self.db.get('SELECT * from topic WHERE id=%s;', id)
        if not t:
            self.write('Have not found topic %s' % id)
            return self.finish()

        if self.current_user.id not in [1, t.user_id]:
            self.write('You have not permission to edit this topic !')
            return self.finish()

        self.d = { 'title': 'Edit topic', 'ERROR': [], 'topic': t,
                   'catalogs': self.db.query('SELECT * from wiki_catalog;') }


    def get(self, id):
        self.render('wiki/edit_topic.html', **self.d)


    def post(self, id):

        d = self.d

        d['name'] = self.get_argument('name', '').encode('utf-8')
        d['catalog'] = int(self.get_argument('catalog', 0))
        d['body'] = self.get_argument('body', '').encode('utf-8')

        if not d['name']:
            d['ERROR'].append('name can not be empty !')
        if not self.d['catalog']:
            d['ERROR'].append('no catalog selected !')
        if not self.d['body']:
            d['ERROR'].append('body can not be empty !')

        if d['ERROR']:
            return self.render('wiki/new_topic.html', **d)

        html = YMK.convert(d['body']).encode('utf-8')

        try:
            self.db.execute(
                "UPDATE topic SET name=%s, body=%s, \
body_html=%s, catalog_id=%s, user_ip=%s, updated='now' \
WHERE id=%s;",
                d['name'], d['body'], html, d['catalog'],
                self.request.remote_ip, id )

            return self.redirect('/wiki/topic/%s' % id)

        except Exception, emsg:
            return self.write('DB error: %s' % emsg)


class DeleteTopic(LyRequestHandler):

    @authenticated
    def get(self, id):

        t = self.db.get('SELECT id, user_id from topic WHERE id=%s;', id)
        if not t:
            return self.write('Have not found topic %s' % id)

        if self.current_user.id not in [1, t.user_id]:
            return self.write('You have not permission to edit this topic !')

        self.db.execute('DELETE FROM topic WHERE id=%s;', id)
        self.write('Delete topic %s success !' % id)



class ViewCatalog(LyRequestHandler):


    def get(self, id):

        c = self.db.get(
            'SELECT * FROM wiki_catalog WHERE id=%s;', id )

        if not c:
            return self.write(u'No catalog %s !' % id)

        ts = self.db.query(
            'SELECT * FROM topic WHERE catalog_id=%s;', id)

        for t in ts:
            t.user = self.db.get(
                'SELECT * FROM auth_user WHERE id=%s;',
                t.user_id )
        
        self.render( 'wiki/view_catalog.html',
                     catalog = c, topics = ts,
                     title = u'View catalog %s' % id )


