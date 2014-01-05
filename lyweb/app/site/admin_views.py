# coding: utf-8

import os
import datetime
import json

from lycustom import LyRequestHandler as RequestHandler, has_permission

from tornado.web import authenticated
from sqlalchemy.sql.expression import asc, desc, func

from ..language.models import Language
from .models import SiteNav, SiteEntry, SiteArticle
from .forms import SiteNavForm, SiteEntryForm, ArticleForm, \
    ArticleEditForm


class Index(RequestHandler):

    @has_permission('admin')
    def get(self):
        self.render('admin/site/index.html')


class NavIndex(RequestHandler):

    title = _('Site Navigation Configure')

    @has_permission('admin')
    def get(self):

        supported_languages = self.application.supported_languages

        cur_locale = self.get_argument(
            'language', self.locale.code )

        navs = self.db.query(SiteNav).order_by( SiteNav.position )

        if cur_locale in supported_languages:

            cur_language = self.db.query(Language).filter_by(
                codename = cur_locale ).first()

            if cur_language:
                navs = navs.filter_by( language_id = cur_language.id )

        d = { 'languages': supported_languages.values(),
              'cur_locale': cur_locale,
              'navs': navs }

        self.render('admin/site/nav.html', **d)


class NavRequestHandler(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.language_list = []
        for L in self.application.supported_languages_list:
            self.language_list.append( (str(L.id), L.name) )

    # TODO:
    def get_entry_url(self, form):

        TYPE = self.get_int(form.type.data)
        url = None

        # type: .models.entry_type

        if TYPE == 1: # URL
            url = form.target.data


        return url
            


class NavAdd(NavRequestHandler):

    title = _('Add Site Navigation')
    template_path = 'admin/site/nav_add.html'

    def get(self):
        form = SiteNavForm(self)
        form.language.choices = self.language_list
        form.process()

        self.render(form = form)

    def post(self):

        form = SiteNavForm(self)
        form.language.choices = self.language_list

        d = { 'form': form }
        if form.validate():
            url = self.get_entry_url( form )
            if url:
                e = SiteNav( url     = url,
                             type    = form.type.data,
                             name    = form.name.data,
                             target  = form.target.data,
                             summary = form.summary.data )

                e.isnewopen = form.isnewopen.data

                ID = self.get_int( form.language.data )
                L = self.db.query(Language).get( ID )
                if L:
                    e.language_id = L.id

                self.db.add(e)
                self.db.commit()
                url = self.reverse_url('admin:site:nav')
                return self.redirect( url )

        self.render(**d)


class NavEdit(NavRequestHandler):

    title = _('Edit Site Navigation')
    template_path = 'admin/site/nav_edit.html'

    def get(self, ID):

        E = self.db.query(SiteNav).get(ID)
        if not E:
            return self.write( _('No such entry: %s') % ID )

        form = SiteNavForm(self)
        form.language.choices = self.language_list
        form.language.default = E.language_id
        form.process()

        form.type.data = E.type
        form.name.data = E.name
        form.target.data = E.target
        form.summary.data = E.summary

        self.render(form = form)

    def post(self, ID):

        E = self.db.query(SiteNav).get(ID)
        if not E:
            return self.write( _('No such entry: %s') % ID )

        form = SiteNavForm(self)
        form.language.choices = self.language_list

        d = { 'form': form }
        if form.validate():
            url = self.get_entry_url( form )
            if url:
                E.url         = url
                E.type        = form.type.data
                E.language_id = form.language.data
                E.name        = form.name.data
                E.target      = form.target.data
                E.isnewopen   = form.isnewopen.data
                E.summary     = form.summary.data
                self.db.add(E)
                self.db.commit()

                url = self.reverse_url('admin:site:nav')
                return self.redirect( url )

        self.render(**d)


class NavDelete(RequestHandler):

    @has_permission('admin')
    def get(self, ID):

        E = self.db.query(SiteNav).get(ID)
        if not E:
            return self.write( _('No such entry: %s') % ID )

        self.db.delete(E)
        self.db.commit()
        self.redirect( self.reverse_url('admin:entry') )


class ajaxNavDelete(RequestHandler):

    @has_permission('admin')
    def post(self):

        success_ids, failed_ids = [], []

        IDS = self.get_argument('ids', [])
        IDS = json.loads(IDS)

        for x in IDS:
            E = self.db.query(SiteNav).get(x)
            if E:
                self.db.delete(E)
                success_ids.append(E.id)
            else:
                failed_ids.append(x)

        self.db.commit()

        data = { 'return_code': 0,
                 'success_ids': success_ids,
                 'failed_ids': failed_ids }

        self.write(data)


class ajaxNavPositionAdjust(RequestHandler):

    ''' Plus of minux position '''

    @has_permission('admin')
    def post(self):

        success_ids, failed_ids = [], []

        IDS = self.get_argument('ids', [])
        IDS = json.loads(IDS)

        plus = self.get_argument_int('plus', 0)

        for x in IDS:
            I = self.db.query(SiteNav).get(x)
            if I:
                I.position = I.position + plus
                success_ids.append(I.id)
            else:
                failed_ids.append(x)

        self.db.commit()

        data = { 'return_code': 0,
                 'success_ids': success_ids,
                 'failed_ids': failed_ids }

        self.write(data)


class EntryIndex(RequestHandler):

    title = _('Site Entry Configure')

    @has_permission('admin')
    def get(self):

        entries = self.db.query(SiteEntry).all()
        d = { 'entries': entries }

        self.render('admin/site/entry.html', **d)


class EntryAdd(NavRequestHandler):

    title = _('Add Site Entry')
    template_path = 'admin/site/entry_add.html'

    def get(self):

        form = SiteEntryForm(self)
        self.render(form = form)

    def post(self):

        form = SiteEntryForm(self)

        d = { 'form': form }
        if form.validate():
            c = self.db.query(SiteEntry).filter_by(
                slug = form.slug.data ).count()
            if c > 0:
                form.slug.errors.append( _('Duplicated slug') )
            else:
                I = SiteEntry(slug = form.slug.data)
                self.db.add(I)
                self.db.commit()

                url = self.reverse_url('admin:site:entry')
                return self.redirect( url )

        self.render(**d)


class EntryEdit(NavRequestHandler):

    title = _('Edit Site Entry')
    template_path = 'admin/site/entry_edit.html'

    def get(self, ID):

        I = self.db.query(SiteEntry).get(ID)
        if not I:
            return self.write( _('No such entry: %s') % ID )

        form = SiteEntryForm(self)
        form.slug.data = I.slug

        self.render(form = form)

    def post(self, ID):

        I = self.db.query(SiteEntry).get(ID)
        if not I:
            return self.write( _('No such entry: %s') % ID )

        form = SiteEntryForm(self)

        d = { 'form': form }
        if form.validate():
            old = self.db.query(SiteEntry).filter_by(
                slug = form.slug.data ).first()
            if old and old.id != I.id:
                form.slug.errors.append( _('Duplicated slug') )
            else:
                I.slug = form.slug.data
                self.db.add(I)
                self.db.commit()

                url = self.reverse_url('admin:site:entry')
                return self.redirect( url )

        self.render(**d)


class ajaxEntryDelete(RequestHandler):

    @has_permission('admin')
    def post(self):

        success_ids, failed_ids = [], []

        IDS = self.get_argument('ids', [])
        IDS = json.loads(IDS)

        for x in IDS:
            I = self.db.query(SiteEntry).get(x)
            if I and len(I.articles) == 0:
                self.db.delete(I)
                success_ids.append(I.id)
            else:
                failed_ids.append(x)

        self.db.commit()

        data = { 'return_code': 0,
                 'success_ids': success_ids,
                 'failed_ids': failed_ids,
                 'failed_string': _('Maybe there are articles exists.') }

        self.write(data)



class ArticleIndex(RequestHandler):

    title = _('Global Article Configure')

    @has_permission('admin')
    def get(self):

        articles = self.db.query(SiteArticle)

        EID = self.get_argument_int('entry', 0)
        E = self.db.query(SiteEntry).get(EID) if EID else None

        if E:
            articles = articles.filter_by(
                entry_id = E.id )
            d = { 'entry': E }

        else:
            supported_languages = self.application.supported_languages

            cur_locale = self.get_argument(
                'language', self.locale.code )


            if cur_locale in supported_languages:

                cur_language = self.db.query(Language).filter_by(
                    codename = cur_locale ).first()

                if cur_language:
                    articles = articles.filter_by( language_id = cur_language.id )

            d = { 'languages': supported_languages.values(),
                  'cur_locale': cur_locale }

        d['articles'] = articles

        self.render('admin/site/article.html', **d)



class ArticleRequestHandler(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.entries_list = []
        for E in self.db.query(SiteEntry).all():
            self.entries_list.append( (str(E.id), E.slug) )

        self.language_list = []
        for L in self.application.supported_languages_list:
            self.language_list.append( (str(L.id), L.name) )


class ArticleAdd(ArticleRequestHandler):

    title = _('Add Article')
    template_path = 'admin/site/article_add.html'

    @has_permission('admin')
    def get(self):

        form = ArticleForm(self)
        form.language.choices = self.language_list
        form.entry.choices = self.entries_list
        form.process()

        self.render(form = form)

    def post(self):
        form = ArticleForm(self)
        form.language.choices = self.language_list
        form.entry.choices = self.entries_list

        d = { 'form': form }
        if form.validate():

            E = self.db.query(SiteEntry).get(
                self.get_int( form.entry.data ) )
            L = self.db.query(Language).get(
                self.get_int( form.language.data ) )

            if E and L:

                old = self.db.query(SiteArticle).filter_by(
                    entry_id = E.id ).filter_by(
                    language_id = L.id ).first()

                if old:
                    form.entry.errors.append( _('This entry was exists!') )
                else:
                    A = SiteArticle( name    = form.name.data,
                                     summary = form.summary.data,
                                     body    = form.body.data )

                    A.entry_id = E.id
                    A.language_id = L.id
                    self.db.add( A )
                    self.db.commit()
                    return self.redirect( self.reverse_url('admin:site:article') )
            else:
                if not E:
                    form.entry.errors.append( _('No such entry.') )
                if not L:
                    form.language.errors.append( _('No such language') )

        self.render( **d )


class ArticleEdit(NavRequestHandler):

    title = _('Edit Site Article')
    template_path = 'admin/site/article_edit.html'

    def get(self, ID):

        I = self.db.query(SiteArticle).get(ID)
        if not I:
            return self.write( _('No such article: %s') % ID )

        form = ArticleEditForm(self)
        form.name.data = I.name
        form.summary.data = I.summary
        form.body.data = I.body
        form.is_visible.data = I.is_visible

        self.render(form = form)

    def post(self, ID):

        I = self.db.query(SiteArticle).get(ID)
        if not I:
            return self.write( _('No such article: %s') % ID )

        form = ArticleEditForm(self)

        d = { 'form': form }
        if form.validate():
            I.name       = form.name.data
            I.summary    = form.summary.data
            I.body       = form.body.data
            I.is_visible = form.is_visible.data
            self.db.add(I)
            self.db.commit()

            url = self.reverse_url('admin:site:article')
            return self.redirect( url )

        self.render(**d)


class ajaxArticleDelete(RequestHandler):

    @has_permission('admin')
    def post(self):

        success_ids, failed_ids = [], []

        IDS = self.get_argument('ids', [])
        IDS = json.loads(IDS)

        for x in IDS:
            I = self.db.query(SiteArticle).get(x)
            if I:
                self.db.delete(I)
                success_ids.append(I.id)
            else:
                failed_ids.append(x)

        self.db.commit()

        data = { 'return_code': 0,
                 'success_ids': success_ids,
                 'failed_ids': failed_ids }

        self.write(data)
