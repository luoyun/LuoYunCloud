# coding: utf-8

import logging, datetime, time
import tornado, markdown
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous



class Index(LyRequestHandler):

    def get(self):
        catalogs = self.db.query('SELECT * from wiki_catalog;')

        for c in catalogs:
            c.topics = self.db.query(
                'SELECT * from topic WHERE catalog_id=%s;',
                c.id )
            for t in c.topics:
                t.user = self.db.get(
                    'SELECT * from auth_user WHERE id=%s;',
                    t.user_id )

        d = { 'title': 'Servers Home', 'catalogs': catalogs }

        self.render('wiki/index.html', **d)


class ViewTopic(LyRequestHandler):

    def get(self, id):

        t = self.db.get('SELECT * from topic WHERE id=%s;', id)
        if not t:
            return self.write('Have not found topic %s' % id)

        t.user = self.db.get(
            'SELECT * from auth_user WHERE id=%s;', t.user_id)

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

    d = { 'title': 'Add new topic' }

    @authenticated
    def get(self):
        self.d['catalogs'] = self.db.query('SELECT * from wiki_catalog;')
        self.render('wiki/new_topic.html', **self.d)

    @authenticated
    def post(self):
        
        d = self.d

        d['name'] = self.get_argument('name', '')
        d['catalog'] = int(self.get_argument('catalog', 0))
        d['body'] = self.get_argument('body', '')

        if not d['name']:
            d['name_error'] = 'name can not be empty !'
        if not self.d['catalog']:
            d['catalog_error'] = 'no catalog selected !'
        if not self.d['body']:
            d['body_error'] = 'body can not be empty !'

        if not (d['name'] and d['body'] and d['catalog']):
            return self.render('wiki/new_topic.html', **d)

        html = markdown.markdown(d['body'])

        try:
            self.db.execute(
                "INSERT INTO topic (name, body, body_html, \
catalog_id, user_id, user_ip, created, updated) VALUES \
(%s, %s, %s, %s, %s, %s, 'now', 'now');",
                d['name'], d['body'], html, d['catalog'],
                self.current_user.id, self.request.remote_ip )
        except Exception, emsg:
            return self.write('Create new topic to DB failed: %s' % emsg)
        
        self.redirect('/wiki')


class EditTopic(LyRequestHandler):

    d = { 'title': 'Edit topic' }

    @authenticated
    def get(self, id):

        self.d['topic'] = self.db.get(
            'SELECT * from topic WHERE id=%s;', id )
        if not self.d['topic']:
            return self.write('Have not found topic %s' % id)

        if not (self.current_user.id == 1 or
                self.current_user.id == self.d['topic'].user_id):
            return self.write('You have not permission to edit this topic !')

        self.d['catalogs'] = self.db.query('SELECT * from wiki_catalog;')

        self.render('wiki/edit_topic.html', **self.d)

    @authenticated
    def post(self, id):

        self.d['topic'] = self.db.get(
            'SELECT * from topic WHERE id=%s;', id )
        if not self.d['topic']:
            return self.write('Have not found topic %s' % id)

        if not (self.current_user.id == 1 or
                self.current_user.id == self.d['topic'].user_id):
            return self.write('You have not permission to edit this topic !')
        
        d = self.d

        d['name'] = self.get_argument('name', '')
        d['catalog'] = int(self.get_argument('catalog', 0))
        d['body'] = self.get_argument('body', '')

        if not d['name']:
            d['name_error'] = 'name can not be empty !'
        if not self.d['catalog']:
            d['catalog_error'] = 'no catalog selected !'
        if not self.d['body']:
            d['body_error'] = 'body can not be empty !'

        if not (d['name'] and d['body'] and d['catalog']):
            return self.render('wiki/new_topic.html', **d)

        html = markdown.markdown(d['body'])

        try:
            self.db.execute(
                "UPDATE topic SET name=%s, body=%s, \
body_html=%s, catalog_id=%s, user_ip=%s, updated='now' \
WHERE id=%s;",
                d['name'], d['body'], html, d['catalog'],
                self.request.remote_ip, id )
        except Exception, emsg:
            return self.write('Update topic failed: %s' % emsg)
        
        self.redirect('/wiki/topic/%s' % id)


class AddCatalog(LyRequestHandler):

    d = { 'title': 'Add appliance catalog' }

    @authenticated
    def get(self):

        # TODO: just admin could add catalog

        self.render('wiki/add_catalog.html', **self.d)

    @authenticated
    def post(self):

        d = self.d

        d['name'] = self.get_argument('name', '')
        d['summary'] = self.get_argument('summary', '')
        d['description'] = self.get_argument('description', '')

        if not d['name']:
            d['name_error'] = 'Name is required !'
            return self.render('appliance/add_catalog.html', **d)

        try:
            self.db.execute(
                "INSERT INTO wiki_catalog (name, summary, description, created, updated) VALUES (%s, %s, %s, 'now', 'now');",
                d['name'], d['summary'], d['description'] )
        except Exception, emsg:
            return self.write('Add catalog to DB failed: %s' % emsg)

        self.redirect('/wiki')
