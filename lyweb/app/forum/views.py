# coding: utf-8

import os, datetime, random, time, re
import tornado
from tornado.web import authenticated
from sqlalchemy.sql.expression import asc, desc, func
from sqlalchemy import and_

from ..auth.models import User
from ..site.models import SiteConfig
from lycustom import RequestHandler as OrigHandler, has_permission

from .models import ForumCatalog, ForumTopic, ForumPost, \
    ForumTopicTag, ForumForbiddenUser, \
    ForumTopicVote, ForumPostVote
from .forms import TopicForm, PostForm

from ytool.pagination import pagination


class RequestHandler(OrigHandler):

    def can_add_topic(self, catalog):

        if not (self.current_user and catalog):
            return False

        if self.current_user in catalog.managers:
            return True

        u = self.db.query(ForumForbiddenUser).filter_by(
            user_id = self.current_user.id ).first()
        if u:
            return False

        if ( catalog.is_private and
             not self.has_permission('admin') and
             not self.current_user in catalog.allowed_users ):
            return False

        return True


    def can_view_topic(self, catalog):

        if not catalog:
            return False

        if ( catalog.is_private or
             not catalog.is_visible ):
            if self.current_user:
                if ( self.current_user in catalog.managers or
                     self.current_user in catalog.allowed_users or
                     self.has_permission('admin') ):
                    return True

        else:
            return True

        return False


    def get_post_parent(self, post):
        if post and post.parent_id:
            return self.db.query(ForumPost).get( post.parent_id )
        return None



class Index(RequestHandler):

    def prepare(self):

        tags = self.db.query(ForumTopicTag).order_by(
            desc('hit') ).limit(30)

        self.prepare_kwargs['TAGS'] = tags


    def get(self):

        tab = self.get_argument('tab', 'topics')

        if tab == 'catalogs':
            self.get_catalogs()

        elif tab == 'topics':
            self.get_topics()

        elif tab == 'topic_votes':
            self.get_topic_votes()

        elif tab == 'posts':
            self.get_posts()

        elif tab == 'post_votes':
            self.get_post_votes()

        # TODO:
        else:
            self.get_catalogs()


    def get_catalogs(self):

        CATALOGS = self.db.query(ForumCatalog).filter_by(
            parent_id = None).order_by( asc('position') ).all()

        for C in CATALOGS:
            C.topic_total = self.db.query(ForumTopic.id).filter_by(
                catalog_id = C.id ).count()

        d = { 'title': _('Forum Catalogs'),
              'can_add_topic': self.can_add_topic,
              'CATALOG_LIST': CATALOGS }

        self.render('forum/index_catalogs.html', **d)


    def get_topics(self):

        page_size = self.get_argument_int('ps', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'created')
        order = self.get_argument_int('order', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        TOPIC_LIST = self.db.query(ForumTopic).join(
            ForumTopic.catalog).filter(
            and_(ForumTopic.status != 1,
                 ForumTopic.is_visible == True,
                 ForumCatalog.is_visible == True,
                 ForumCatalog.is_private == False))

        if by == 'created':
            by = ForumTopic.created
        elif by == 'updated':
            by = ForumTopic.updated
        else:
            by = ForumTopic.id

        total = TOPIC_LIST.count()

        sort_by_obj = desc(by) if order else asc(by)

        TOPIC_LIST = TOPIC_LIST.order_by(
            sort_by_obj).slice(start, stop).all()

        page_html = pagination(
            self.request.uri, total, page_size, cur_page )

        d = { 'title': _('Forum Catalog Home'),
              'TOPIC_LIST': TOPIC_LIST,
              'TOPIC_TOTAL': total,
              'page_html': page_html }

        self.render('forum/index_topics.html', **d)


    def get_topic_votes(self):

        page_size = self.get_argument_int('ps', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'created')
        order = self.get_argument_int('order', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        VOTE_LIST = self.db.query(ForumTopicVote)

        if by not in ['id', 'created', 'updated']:
            by = 'id'

        total = VOTE_LIST.count()

        sort_by_obj = desc(by) if order else asc(by)
        VOTE_LIST = VOTE_LIST.order_by(
            sort_by_obj).slice(start, stop).all()

        page_html = pagination(
            self.request.uri, total, page_size, cur_page )

        d = { 'title': _('Forum Topic Vote History'),
              'VOTE_LIST': VOTE_LIST,
              'VOTE_TOTAL': total,
              'page_html': page_html }

        self.render('forum/index_topic_votes.html', **d)


    def get_posts(self):

        page_size = self.get_argument_int('ps', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'created')
        order = self.get_argument_int('order', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        POST_LIST = self.db.query(ForumPost)

        if by not in ['id', 'created', 'updated']:
            by = 'id'

        total = POST_LIST.count()

        sort_by_obj = desc(by) if order else asc(by)
        POST_LIST = POST_LIST.order_by(
            sort_by_obj).slice(start, stop).all()

        page_html = pagination(
            self.request.uri, total, page_size, cur_page )

        d = { 'title': _('Forum Catalog Home'),
              'POST_LIST': POST_LIST,
              'POST_TOTAL': total,
              'get_post_parent': self.get_post_parent,
              'page_html': page_html }

        self.render('forum/index_posts.html', **d)


    def get_post_votes(self):

        page_size = self.get_argument_int('ps', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'created')
        order = self.get_argument_int('order', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        VOTE_LIST = self.db.query(ForumPostVote)

        if by not in ['id', 'created', 'updated']:
            by = 'id'

        total = VOTE_LIST.count()

        sort_by_obj = desc(by) if order else asc(by)
        VOTE_LIST = VOTE_LIST.order_by(
            sort_by_obj).slice(start, stop).all()

        page_html = pagination(
            self.request.uri, total, page_size, cur_page )

        d = { 'title': _('Forum Post Vote History'),
              'VOTE_LIST': VOTE_LIST,
              'VOTE_TOTAL': total,
              'page_html': page_html }

        self.render('forum/index_post_votes.html', **d)



class CatalogIndex(RequestHandler):

    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me catalog id please.') )

        CATALOG = self.db.query(ForumCatalog).get(ID)
        if not CATALOG:
            return self.write( _('No such catalog %s') % ID )

        if CATALOG.is_private:
            if not CATALOG.is_visible:
                return self.write( _('Catalog is private and not visible.') )

        page_size = self.get_argument_int('ps', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'created')
        order = self.get_argument_int('order', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        TOPIC_LIST = self.db.query(ForumTopic).filter(
            and_( ForumTopic.catalog_id == ID,
                  ForumTopic.status != 1 ) )

        if by not in ['id', 'created', 'updated']:
            by = 'id'

        total = TOPIC_LIST.count()

        sort_by_obj = desc(by) if order else asc(by)
        TOPIC_LIST = TOPIC_LIST.order_by(
            sort_by_obj).slice(start, stop).all()


        page_html = pagination(
            self.request.uri, total, page_size, cur_page )

        d = { 'title': _('Forum Catalog Home'),
              'can_add_topic': self.can_add_topic,
              'CATALOG': CATALOG,
              'TOPIC_LIST': TOPIC_LIST,
              'TOPIC_TOTAL': total,
              'page_html': page_html }

        self.render('forum/catalog_index.html', **d)



class TopicHandler(RequestHandler):

    def update_tag(self, tag, topic):
        restr = r',|，|:|：|\|'
        tags = [ x.strip() for x in re.split(restr, tag)
                 if x.strip() != '' ]

        old_id_list = [ x.id for x in topic.tags]
        taglist = []
        # TODO: dotag is ugly.
        dotag = []
        for tagname in tags:
            if tagname in dotag: continue
            dotag.append(tagname)
            T = self.db.query(ForumTopicTag).filter(
                func.lower(ForumTopicTag.name) == tagname.lower() ).first()
            if T:
                if T.id not in old_id_list:
                    T.hit += 1
            else:
                T = ForumTopicTag( name = tagname )
                self.db.add(T)
            taglist.append( T )
        topic.tags = taglist

        # delete hit
        new_id_list = [ x.id for x in topic.tags]
        for ID in old_id_list:
            if ID not in new_id_list:
                T = self.db.query(ForumTopicTag).get(ID)
                if T.hit == 1:
                    self.db.delete(T)
                else:
                    T.hit -= 1

        self.db.commit()


    def get_my_topic_byid(self, ID):
        if ID:
            t = self.db.query(ForumTopic).get(ID)
            if t:
                if ( t.user_id == self.current_user.id or
                     self.has_permission('admin') ):
                    return t

        return None



class TopicAdd(TopicHandler):

    template_path = 'forum/topic/edit.html'

    @authenticated
    def prepare(self):

        self.CATALOG = None

        cid = self.get_argument_int('cid', None)
        if cid:
            self.CATALOG = self.db.query(ForumCatalog).get(cid)

        if self.CATALOG and not self.can_add_topic( self.CATALOG ):
            return self.finish( _('No permission to add topic in "%s"') % self.CATALOG.name )

        form = TopicForm(self)

        catalog_choices = []
        for c in self.db.query(ForumCatalog).filter(
            and_(ForumCatalog.is_visible == True,
                 ForumCatalog.is_private == False)):
            catalog_choices.append( (str(c.id), c.name) )

        form.catalog.choices = catalog_choices

        self.prepare_kwargs['can_add_topic'] = self.can_add_topic
        self.prepare_kwargs['CATALOG'] = self.CATALOG
        self.prepare_kwargs['form'] = form
        self.prepare_kwargs['markup_language'] = self.get_argument(
            'markup_language', 'WYSIWYM')

        self.prepare_kwargs['title'] = _('Post A New Topic')


    def get(self):

        form = self.prepare_kwargs['form']
        if self.CATALOG:
            form.catalog.default = self.CATALOG.id
            form.process()

        self.render()


    def post(self):
        form = self.prepare_kwargs['form']

        if form.validate():
            topic = ForumTopic( name = form.name.data,
                                summary = form.summary.data,
                                body = form.body.data )
            topic.user = self.current_user

            if self.CATALOG:
                topic.catalog_id = self.CATALOG.id
            else:
                topic.catalog_id = form.catalog.data

            ml = self.prepare_kwargs['markup_language']
            if ml == 'WYSIWYM':
                topic.markup_language = 2

            self.db.add(topic)
            self.db.commit()
            self.update_tag(form.tag.data, topic)

            url = self.reverse_url('forum:catalog')
            url += '?id=%s' % topic.catalog_id
            return self.redirect( url )

        self.render()



class TopicEdit(TopicHandler):

    template_path = 'forum/topic/edit.html'

    @authenticated
    def prepare(self):

        ID = self.get_argument_int('id', None)
        t = self.get_my_topic_byid( ID )
        if not t:
            return self.finish( _('Can not find topic: %s') % ID )

        form = TopicForm(self)

        catalog_choices = []
        for c in self.db.query(ForumCatalog).filter(
            and_(ForumCatalog.is_visible == True,
                 ForumCatalog.is_private == False)):
            catalog_choices.append( (str(c.id), c.name) )

        form.catalog.choices = catalog_choices

        self.prepare_kwargs['form'] = form
        self.prepare_kwargs['TOPIC'] = t
        self.prepare_kwargs['title'] = _('Edit Topic: "%s"') % t.name
        self.prepare_kwargs['markup_language'] = t.language


    def get(self):

        form = self.prepare_kwargs['form']
        T = self.prepare_kwargs['TOPIC']

        form.catalog.default = T.catalog_id
        form.process()

        form.name.data = T.name
        form.summary.data = T.summary
        form.tag.data = ', '.join([ x.name for x in T.tags ])
        form.body.data = T.body

        self.render()


    def post(self):

        form = self.prepare_kwargs['form']
        T = self.prepare_kwargs['TOPIC']

        if form.validate():
            T.catalog_id = form.catalog.data
            T.name = form.name.data
            T.summary = form.summary.data
            T.body = form.body.data

            self.db.commit()
            self.update_tag(form.tag.data, T)

            url = self.reverse_url('forum:topic:view')
            url += '?id=%s' % T.id
            return self.redirect(url)

        self.render()



class TopicDelete(RequestHandler):

    @authenticated
    def post(self):

        d = { 'ret_code': 1,
              'ret_string': _('Something is wrong.') }

        ID = self.get_argument_int('id', None)
        if not ID:
            d['ret_string'] = _('Give me topic id please.')
            return self.finish( d )

        T = self.db.query(ForumTopic).get(ID)
        if not T:
            d['ret_string'] = _('No such topic: %s') % ID
            return self.finish( d )

        if ( T.user_id != self.current_user.id and
             not self.has_permission('admin') ):
            d['ret_string'] = _('No permissions !')
            return self.finish( d )

        # TODO: more check and status update for delete a topic

        CID = T.catalog_id

        # tags
        for tag in T.tags:
            if tag.hit == 1:
                self.db.delete(tag)
            else:
                tag.hit -= 1

        #self.db.delete(T)
        T.set_status('deleted')
        self.db.commit()

        url = self.reverse_url('forum:catalog')
        url += '?id=%s' % CID

        d['ret_string'] = _('Delete topic success.') + \
            '<a href="' + url + '">' + _('Go Home') + '</a>'
        self.write( d )



class TopicView(RequestHandler):

    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me topic id please.') )

        topic = self.db.query(ForumTopic).get(ID)
        if not topic:
            return self.write( _('No such topic: %s') % ID )

        if topic.is_deleted:
            return self.write( _('Topic %s is deleted') % ID )

        if not self.can_view_topic( topic.catalog ):
            return self.write( _('No permission to view topic %s') % ID )

        t = self.get_argument('t', None)
        if t in ['source']:
            if t == 'source':
                #self.set_header("Content-Type", "text/plain")
                #return self.write(topic.body)
                return self.render('forum/topic/output/source.html', TOPIC = topic)

        topic.visit += 1
        self.db.commit()

        POSTS = self.db.query(ForumPost).filter_by(
            topic_id = topic.id).order_by(desc('updated'))

        post_total = self.db.query(ForumPost.id).filter_by(
            topic_id = topic.id).count()

        d = { 'title': _('View Topic: %s') % topic.name,
              'get_post_parent': self.get_post_parent,
              'POST_TOTAL': post_total,
              'TOPIC': topic, 'POSTS': POSTS,
              'BODY_MARKUP': 'markdown' }

        self.render('forum/topic/view.html', **d)



class TopicReply(TopicHandler):

    title = _('Reply Topic')
    template_path = 'forum/topic/reply.html'

    @authenticated
    def prepare(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give topic id please.') )

        T = self.db.query(ForumTopic).get(ID)
        if not T:
            return self.finish( _('No such topic: %s') % ID )

        if T.is_locked:
            return self.finish( _('Topic %s is locked.') % ID )

        if not T.is_visible:
            return self.finish( _('Topic %s is not visible.') % ID )

        dateline = datetime.datetime.now() - datetime.timedelta( seconds = 30 )

        P = self.db.query(ForumPost).filter(
            and_( ForumPost.user_id == self.current_user.id,
                  ForumPost.updated > dateline ) ).first()

        if P:
            return self.finish( _('Your speech is too fast!') )

        self.prepare_kwargs['form'] = PostForm(self)
        self.prepare_kwargs['TOPIC'] = T


    def get(self):
        self.render()


    def post(self):

        form = self.prepare_kwargs['form']
        T = self.prepare_kwargs['TOPIC']

        if form.validate():

            post = ForumPost( topic = T, body = form.body.data )
            post.user_id = self.current_user.id

            self.db.add(post)
            self.db.commit()

            # TODO: test reply
            if self.current_user.id != T.user_id:
                self.topic_reply_notice( T, post )

            url = self.reverse_url('forum:topic:view')
            url += '?id=%s' % T.id

            return self.redirect( url )

        self.render()


    def topic_reply_notice(self, topic, post):

        subject = _('[LYC] Your topic "%(name)s" have replyed by %(who)s') % {
            'name': topic.name, 'who': self.current_user.username }

        host = SiteConfig.get(
            self.db, 'registration.host', 'http://127.0.0.1')

        d = { 'return_string': True, 'TOPIC': topic, 'POST': post,
              'host': host }
        body = self.render('forum/topic/reply_notice.html', **d)

        response = self.sendmsg(
            uri = 'mailto.address',
            data = { 'to_user_id': topic.user_id,
                     'subject': subject,
                     'body': body } )
        return response



class TopicVote(TopicHandler):

    @authenticated
    def post(self):

        d = { 'ret_code': 1,
              'ret_string': _('Something is wrong.') }

        ID = self.get_argument_int('id', None)
        if not ID:
            d['ret_string'] = _('Give me topic id please.')
            return self.write( d )

        T = self.db.query(ForumTopic).get(ID)
        if not T:
            d['ret_string'] = _('No such topic: %s') % ID
            return self.write( d )

        if T.user_id == self.current_user.id:
            d['ret_string'] = _('Can not vote yourself')
            return self.write( d )

        vote = self.get_argument_int('vote', 0)

        V = self.db.query(ForumTopicVote).filter(
            and_( ForumTopicVote.topic_id == T.id,
                  ForumTopicVote.user_id == self.current_user.id )
            ).first()

        if V:
            if vote > 0:
                if V.value < 0:
                    T.unlike -= 1
                    T.like += 1
                    V.value = vote
                else:
                    d['ret_string'] = _('Voted already.')
                    return self.write( d )

            elif vote < 0:
                if V.value > 0:
                    T.like -= 1
                    T.unlike += 1
                    V.value = vote
                else:
                    d['ret_string'] = _('Voted already.')
                    return self.write( d )

        else:
            if vote > 0:
                T.like += 1

            elif vote < 0:
                T.unlike += 1

            V = ForumTopicVote( topic_id = T.id, value = vote,
                                user_id = self.current_user.id )
            self.db.add( V )

        self.db.commit()

        d['ret_string'] = _('Voted success.')
        d['ret_code'] = 0
        d['like'] = T.like
        d['unlike'] = T.unlike
        self.write( d )



class PostVote(RequestHandler):

    @authenticated
    def post(self):

        d = { 'ret_code': 1,
              'ret_string': _('Something is wrong.') }

        ID = self.get_argument_int('id', None)
        if not ID:
            d['ret_string'] = _('Give me post id please.')
            return self.write( d )

        P = self.db.query(ForumPost).get(ID)
        if not P:
            d['ret_string'] = _('No such post: %s') % ID
            return self.write( d )

        if P.user_id == self.current_user.id:
            d['ret_string'] = _('Can not vote yourself')
            return self.write( d )

        vote = self.get_argument_int('vote', 0)

        V = self.db.query(ForumPostVote).filter(
            and_( ForumPostVote.post_id == P.id,
                  ForumPostVote.user_id == self.current_user.id )
            ).first()

        if V:
            if vote > 0:
                if V.value < 0:
                    P.like += 1
                    P.unlike -= 1
                    V.value = vote
                else:
                    d['ret_string'] = _('Voted already.')
                    return self.write( d )

            elif vote < 0:
                if V.value > 0:
                    P.like -= 1
                    P.unlike += 1
                    V.value = vote
                else:
                    d['ret_string'] = _('Voted already.')
                    return self.write( d )

        else:
            if vote > 0:
                P.like += 1

            elif vote < 0:
                P.unlike += 1

            V = ForumPostVote( post_id = P.id, value = vote,
                               user_id = self.current_user.id )
            self.db.add( V )

        self.db.commit()

        d['ret_string'] = _('Voted success.')
        d['ret_code'] = 0
        d['like'] = P.like
        d['unlike'] = P.unlike
        self.write( d )



class PostReply(RequestHandler):

    title = _('Reply Post')
    template_path = 'forum/post/edit.html'

    @authenticated
    def prepare(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give post id please.') )

        P = self.db.query(ForumPost).get(ID)
        if not P:
            return self.finish( _('No such post: %s') % ID )

        if P.is_locked:
            return self.finish( _('Post %s is locked.') % ID )

        if not P.is_visible:
            return self.finish( _('Post %s is not visible.') % ID )

        dateline = datetime.datetime.now() - datetime.timedelta( seconds = 30 )

        recent = self.db.query(ForumPost).filter(
            and_( ForumPost.user_id == self.current_user.id,
                  ForumPost.updated > dateline ) ).first()

        if recent:
            return self.finish( _('Your speech is too fast!') )

        self.prepare_kwargs['form'] = PostForm(self)
        self.prepare_kwargs['REPLY_POST'] = P


    def get(self):
        self.render()


    def post(self):

        form = self.prepare_kwargs['form']
        P = self.prepare_kwargs['REPLY_POST']

        if form.validate():

            post = ForumPost( topic = P.topic,
                              body = form.body.data )
            post.user_id = self.current_user.id
            post.parent_id = P.id

            self.db.add(post)
            self.db.commit()

            # TODO: test reply
            if self.current_user.id != P.user_id:
                self.post_reply_notice( P )

            url = self.reverse_url('forum:topic:view')
            url += '?id=%s' % P.topic_id

            return self.redirect( url )

        self.render()


    def post_reply_notice(self, post):

        topic = post.topic

        subject = _('[LYC] Your post for "%(topic)s" have replyed by %(who)s') % {
            'topic': topic.name, 'who': self.current_user.username }

        host = SiteConfig.get(
            self.db, 'registration.host', 'http://127.0.0.1')

        d = { 'return_string': True, 'TOPIC': topic, 'POST': post,
              'host': host }

        body = self.render('forum/post/reply_notice.html', **d)

        response = self.sendmsg(
            uri = 'mailto.address',
            data = { 'to_user_id': post.user_id,
                     'subject': subject,
                     'body': body } )
        return response



class PostEdit(RequestHandler):

    title = _('Edit Post')
    template_path = 'forum/post/edit.html'

    @authenticated
    def prepare(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give post id please.') )

        P = self.db.query(ForumPost).get(ID)
        if not P:
            return self.finish( _('No such post: %s') % ID )

        if ( P.user_id != self.current_user.id and
             not self.has_permission('admin') ):
            return self.finish( _('No permission to edit post %s') % ID )

        self.prepare_kwargs['form'] = PostForm(self)
        self.prepare_kwargs['POST'] = P


    def get(self):

        form = self.prepare_kwargs['form']
        P = self.prepare_kwargs['POST']

        form.body.data = P.body

        self.render()


    def post(self):

        form = self.prepare_kwargs['form']
        P = self.prepare_kwargs['POST']

        if form.validate():

            P.body = form.body.data
            self.db.commit()

            self.post_update_notice( P )

            url = self.reverse_url('forum:topic:view')
            url += '?id=%s' % P.topic_id

            return self.redirect( url )

        self.render()


    def post_update_notice(self, post):

        topic = post.topic

        subject = _('[LYC] %(who)s" update post for %(topic)s') % {
            'topic': topic.name, 'who': self.current_user.username }

        host = SiteConfig.get(
            self.db, 'registration.host', 'http://127.0.0.1')

        d = { 'return_string': True, 'TOPIC': topic, 'POST': post,
              'host': host }
        body = self.render('forum/post/update_notice.html', **d)

        response = self.sendmsg(
            uri = 'mailto.address',
            data = { 'to_user_id': topic.user_id,
                     'subject': subject,
                     'body': body } )
        return response



class TagHome(RequestHandler):

    def get(self):

        TAGS = self.db.query(ForumTopicTag).order_by( desc('hit') )
        tag_total = self.db.query(ForumTopicTag.id).count()

        d = { 'title': _('Forum Tag Home'),
              'TAG_TOTAL': tag_total, 'TAGS': TAGS }

        self.render('forum/tag/index.html', **d)



class TagView(RequestHandler):

    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me tag id please.') )

        TAG = self.db.query(ForumTopicTag).get(ID)
        if not TAG:
            return self.write( _('No such tag %s') % ID )

        page_size = self.get_argument_int('ps', 20)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'created')
        order = self.get_argument_int('order', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        TOPICS = self.db.query(ForumTopic).filter(
            ForumTopic.tags.contains(TAG) )

        if by not in ['id', 'created', 'updated']:
            by = 'id'

        total = TOPICS.count()

        sort_by_obj = desc(by) if order else asc(by)
        TOPICS = TOPICS.order_by(sort_by_obj).slice(start, stop)

        TAGS = self.db.query(ForumTopicTag).order_by(
            desc('hit') ).limit(30)

        page_html = pagination(self.request.uri, total, page_size, cur_page)

        d = { 'title': _('Forum Tag Home'),
              'TAG': TAG, 'TAGS': TAGS, 'TOPIC_LIST': TOPICS,
              'TOPIC_TOTAL': total, 'page_html': page_html }

        self.render('forum/tag/view.html', **d)

