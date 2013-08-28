# coding: utf-8

import os
import datetime
import json

from lycustom import RequestHandler as RequestHandler, has_permission

from tornado.web import authenticated
from sqlalchemy.sql.expression import asc, desc, func
from sqlalchemy import and_

from ..language.models import Language
from .models import SiteNav, SiteEntry, SiteArticle, SiteConfig, \
    SiteLocaleConfig, SiteJob
from .forms import SiteNavForm, SiteEntryForm, ArticleForm, \
    ArticleEditForm, SiteConfigForm, SiteLocaleConfigForm

from yweb.utils.pagination import pagination

import settings



class Index(RequestHandler):

    @has_permission('admin')
    def get(self):
        self.render('admin/site/index.html')


class NavIndex(RequestHandler):

    title = _('Site Navigation Configure')

    @has_permission('admin')
    def get(self):

        cur_locale = self.get_argument('language', self.locale.code)

        navs = self.db.query(SiteNav).order_by( SiteNav.position )

        if cur_locale in settings.LANGUAGES:

            L = self.db.query(Language).filter_by(
                codename = cur_locale ).first()

            if L:
                navs = navs.filter_by( language_id = L.id )

        d = { 'cur_locale': cur_locale, 'navs': navs }

        self.render('admin/site/nav.html', **d)


class NavRequestHandler(RequestHandler):

    @has_permission('admin')
    def prepare(self):

        self.language_list = []

        for codename in settings.LANGUAGES:
            L = self.db.query(Language).filter_by(
                codename = codename).first()
            if L:
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
            languages = settings.LANGUAGES

            cur_locale = self.get_argument(
                'language', self.locale.code )


            if cur_locale in languages:

                cur_language = self.db.query(Language).filter_by(
                    codename = cur_locale ).first()

                if cur_language:
                    articles = articles.filter_by( language_id = cur_language.id )

            d = { 'languages': languages,
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
        for codename in settings.LANGUAGES:
            L = self.db.query(Language).filter_by(
                codename = codename).first()
            if L:
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



class ConfigIndex(RequestHandler):

    title = _('Global Site Config')

    @has_permission('admin')
    def get(self):
        d = {'configs': self.db.query(SiteConfig).all()}
        self.render('admin/site/config/index.html', **d)


class ConfigEdit(RequestHandler):

    title = _('Edit Site Config')
    template_path = 'admin/site/config/edit.html'

    @has_permission('admin')
    def get(self):

        form = SiteConfigForm(self)

        key = self.get_argument('key', None)
        it = self.db.query(SiteConfig).filter_by(key=key).first()

        if it:
            form.key.data = key
            form.value.data = it.value

        self.render( form = form )


    @has_permission('admin')
    def post(self):

        form = SiteConfigForm(self)

        if form.validate():

            it = self.db.query(SiteConfig).filter_by(
                key = form.key.data.strip() ).first()

            if it:
                it.value = form.value.data.strip()

            else:
                it = SiteConfig( key = form.key.data.strip(),
                                  value = form.value.data.strip() )
            self.db.add(it)
            self.db.commit()
            url = self.reverse_url('admin:site:config')
            return self.redirect_next( url )

        self.render( form = form )



class ConfigDelete(RequestHandler):

    @has_permission('admin')
    def get(self):

        key = self.get_argument('key', None)
        if not key:
            return self.write( _('No config key found.') )

        it = self.db.query(SiteConfig).filter_by(key=key).first()
        if it:
            self.db.delete(it)
            self.db.commit()
            self.redirect_next( self.reverse_url('admin:site:config') )
        else:
            self.write( _('No such config for key: %s') % key )



class LocaleConfigIndex(RequestHandler):

    title = _('Global Locale Site Config')

    @has_permission('admin')
    def get(self):
        d = {'configs': self.db.query(SiteLocaleConfig).all()}
        self.render('admin/site/localeconfig/index.html', **d)


class LocaleConfigEdit(RequestHandler):

    title = _('Edit Site Locale Config')
    template_path = 'admin/site/localeconfig/edit.html'

    @has_permission('admin')
    def prepare(self):

        self.language_list = []
        for codename in settings.LANGUAGES:
            L = self.db.query(Language).filter_by(
                codename = codename).first()
            if L:
                self.language_list.append( (str(L.id), L.name) )


    def get(self):

        form = SiteLocaleConfigForm(self)
        form.language.choices = self.language_list
        form.language.default = self.language.id
        form.process()

        form.key.data = self.get_argument('key', None)

        ID = self.get_argument('ID', 0)
        if ID:
            it = self.db.query(SiteLocaleConfig).get(ID)
            if it:
                form.language.default = it.language_id
                form.process()
                form.key.data = it.key
                form.value.data = it.value

        self.render( form = form )


    def post(self):

        form = SiteLocaleConfigForm(self)
        form.language.choices = self.language_list

        if form.validate():

            it = self.db.query(SiteLocaleConfig).filter(
                and_(SiteLocaleConfig.key == form.key.data.strip(),
                     SiteLocaleConfig.language_id == form.language.data
                     )).first()

            if it:
                it.value = form.value.data.strip()
                it.language_id = form.language.data
            else:
                it = SiteLocaleConfig(
                    key = form.key.data.strip(),
                    value = form.value.data.strip(),
                    language_id = form.language.data )

            self.db.add(it)
            self.db.commit()

            url = self.reverse_url('admin:site:localeconfig')
            return self.redirect_next( url )

        self.render( form = form )


class LocaleConfigDelete(RequestHandler):

    @has_permission('admin')
    def get(self, ID):

        it = self.db.query(SiteLocaleConfig).get(ID)
        if it:
            self.db.delete(it)
            self.db.commit()
            self.redirect_next( self.reverse_url('admin:site:localeconfig') )
        else:
            self.write( _('No such locale config : %s') % ID )



class SiteJobIndex(RequestHandler):

    title = _('Site Job')

    @has_permission('admin')
    def get(self):

        by = self.get_argument('by', 'id')
        order = self.get_argument_int('order', 1)
        status = self.get_argument('status', None)
        page_size = self.get_argument_int('sepa', 50)
        cur_page = self.get_argument_int('p', 1)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        jobs = self.db.query(SiteJob)

        if by not in ['id', 'created', 'updated']:
            by = 'id';

        by = desc(by) if order else asc(by)
        jobs = jobs.order_by( by )

        total = jobs.count()

        jobs = jobs.slice(start, stop)

        page_html = pagination(self.request.uri, total, page_size, cur_page)

        d = { 'PAGE_HTML': page_html,
              'status': status,
              'JOB_LIST': jobs }

        self.render('admin/site/job/index.html', **d)


class SiteJobView(RequestHandler):

    title = _('Site Job View')

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give me site job id please.') )

        J = self.db.query(SiteJob).get( ID )
        if not J:
            return self.write( _('Can not find site job %s') % ID )

        ajax = self.get_argument('ajax', False)

        if ajax:
            d = { 'id': J.id,
                  'user_id': J.user_id,
                  'status': J.status,
                  'desc': J.desc,
                  'text': J.text }
            self.write( d )

        else:
            d = { 'JOB': J }
            self.render('admin/site/job/view.html', **d)
