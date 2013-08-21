# coding: utf-8

import logging, datetime, time, re

from lycustom import RequestHandler

from tornado.web import authenticated, asynchronous

from app.auth.models import User, Group
from app.auth.utils import enc_login_passwd
from app.site.models import SiteConfig

from app.account.models import UserProfile, UserResetpass

from app.resource.models import Resource
from app.instance.models import Instance
from app.job.models import Job

from app.account.forms import ResetPassForm

from app.admin.forms import CreateUserForm, UserGroupEditForm, \
    ResourceForm, ResourceSimpleForm

import random, time, pickle, base64
from hashlib import md5, sha512, sha1

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_, or_

from lycustom import has_permission

from settings import ADMIN_USER_LIST_PAGE_SIZE as USER_PS
import settings

from yweb.utils.pagination import pagination
from app.resource.utils import resource_mail_notice



class Index(RequestHandler):

    @has_permission('admin')
    def get(self):

        page_size = self.get_argument_int('sepa', USER_PS)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        order = self.get_argument_int('order', 1)
        gid = self.get_argument_int('gid', -1)
        search = self.get_argument('search', False)

        UL = self.db.query(User)

        if by == 'id':
            by_obj = User.id
        elif by == 'date_joined':
            by_obj = User.date_joined
        elif by == 'last_login':
            by_obj = User.last_login
        elif by == 'last_active':
            by_obj = User.last_active
        elif by == 'username':
            by_obj = User.username
        elif by == 'is_locked':
            by_obj = User.is_locked
        elif by == 'description':
            by_obj = User.id
            UL = UL.filter( User.description != None )
        else:
            by_obj = User.id

        by_exp = desc(by_obj) if order else asc(by_obj)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        if search:
            search = '%' + search + '%'
            UL = UL.filter( or_(User.username.like(search),
                                User.email.like(search) ) )

        GROUP = None
        if gid == 0:
            UL = UL.filter( ~User.groups.any() )
        elif gid > 0:
            GROUP = self.db.query(Group).get(gid)
            if GROUP:
                UL = UL.filter( User.groups.contains(GROUP) )

        UL = UL.order_by( by_exp )

        total = UL.count()
        UL = UL.slice(start, stop)

        page_html = pagination(self.request.uri, total,
                               page_size, cur_page,
                               sepa_range = [20, 50, 100])

        def sort_by(by):
            return self.urlupdate(
                { 'by': by, 'order': 1 if order == 0 else 0 })
            
        d = { 'title': self.trans(_('Admin User Management')),
              'sort_by': sort_by,
              'SORT_BY': by,
              'ORDER': order,
              'urlupdate': self.urlupdate,
              'USER_LIST': UL, 'PAGE_HTML': page_html,
              'TOTAL_USER': total,
              'PAGE_SIZE': page_size,
              'GROUP': GROUP, 'GID': gid,
              'GROUP_LIST': self.db.query(Group).all()}

        if self.get_argument('ajax', None):
            self.render( 'admin/user/index.ajax.html', **d )
        else:
            self.render( 'admin/user/index.html', **d )



class UserAdd(RequestHandler):

    title = _('Create New User')
    template_path = 'admin/user/add.html'

    @has_permission('admin')
    def get(self):
        self.render( form = CreateUserForm(self) )
    

    @has_permission('admin')
    def post(self):

        form = CreateUserForm(self)

        if form.validate():

            user = self.db.query(User).filter_by(
                username=form.username.data ).first()

            if user:
                form.username.errors.append(
                    _('This username is occupied') )
            else:
                enc_password = enc_login_passwd(form.password.data)

                new = User( username = form.username.data,
                            password = enc_password )
                self.db.add( new )
                self.db.commit()

                new.init_account(self.db)

                profile = UserProfile( new )
                self.db.add(profile)
                self.db.commit()

                url = self.reverse_url('admin:user:view')
                url += '?id=%s' % new.id
                return self.redirect( url )

        self.render( form = form )



class View(RequestHandler):

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', 0)
        user = self.db.query(User).get(ID)
        if not user:
            return self.write( _('No such user: %s') % ID )

        profile = user.profile
        # TODO: profile is None

        resource_total = profile.get_resource_total()
        resource_used = profile.get_resource_used()

        d = { 'title': _('View User %s') % user.username,
              'resource_total': resource_total,
              'resource_used': resource_used,
              'USER': user }

        self.render( 'admin/user/view.html', **d)



class ResetPass(RequestHandler):

    title = _('Reset User Password')
    template_path = 'admin/user/reset_password.html'

    @has_permission('admin')
    def prepare(self):
        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give me user id please.') )

        U = self.db.query(User).get(ID)
        if not U:
            return self.finish( _('Can not find user %s') % ID )

        self.prepare_kwargs['USER'] = U
        self.prepare_kwargs['form'] = ResetPassForm(self)


    def get(self):
        self.render()


    def post(self):

        form = self.prepare_kwargs['form']
        U = self.prepare_kwargs['USER']

        if form.validate():
            U.password = enc_login_passwd(form.password.data)
            self.db.commit()

            url = self.reverse_url('admin:user:view')
            url += '?id=%s' % U.id
            return self.redirect( url )

        self.render()



class GroupEdit(RequestHandler):

    title = _('Edit User Group')
    template_path = 'admin/user/group_edit.html'

    @has_permission('admin')
    def prepare(self):

        ID = self.get_argument_int('id', 0)
        self.user = self.db.query(User).get(ID)
        if not self.user:
            self.write( _('No such user: %s') % ID )
            return self.finish()

        self.default_choices = []
        group_choices = []
        for G in self.db.query(Group).all():
            group_choices.append( (G.name, G.name) )
            if G in self.user.groups:
                self.default_choices.append( G.name )

        self.form = UserGroupEditForm(self)
        self.form.groups.choices = group_choices

        self.prepare_kwargs['USER'] = self.user
        self.prepare_kwargs['form'] = self.form


    def get(self):

        self.form.groups.default = self.default_choices
        self.form.process()

        self.render()


    def post(self):

        user = self.user

        if self.form.validate():
            groups = self.request.arguments.get('groups', [])
            group_obj = []

            for name in groups:
                G = self.db.query(Group).filter_by(name=name).first()
                if G: group_obj.append( G )

            user.groups = group_obj
            self.db.add(user)
            self.db.commit()

            url = self.reverse_url('admin:user:view')
            url += '?id=%s' % user.id
            return self.redirect( url )

        self.render()


class ResourceAdd(RequestHandler):

    title = _('Add Resource For User')
    template_path = 'admin/user/resource_add.html'

    @has_permission('admin')
    def prepare(self):

        ID = self.get_argument_int('id', 0)
        self.user = self.db.query(User).get(ID)
        if not self.user:
            self.write( _('No such user: %s') % ID )
            return self.finish()

        type_choices = []
        for x, y in Resource.RESOURCE_TYPE:
            type_choices.append( (str(x), y) )

        self.form = ResourceForm(self)
        self.form.type.choices = type_choices

        self.prepare_kwargs['form'] = self.form
        self.prepare_kwargs['USER'] = self.user

    def get(self):

        self.form.process()
        self.render()

    def post(self):

        form = self.form
        user = self.user

        if form.validate():
            new = Resource( user = user,
                            rtype = form.type.data,
                            size = form.size.data,
                            effect_date = form.effect_date.data,
                            expired_date = form.expired_date.data )
            self.db.add( new )
            self.db.commit()

            # count be choices, email notice
            resource_mail_notice(self, user)

            url = self.reverse_url('admin:user:view')
            url += '?id=%s' % user.id
            return self.redirect( url )

        self.render()



class ResourceHandler(RequestHandler):

    @has_permission('admin')
    def initialize(self):

        self.U = None

        ID = self.get_argument_int('id', 0)
        U = self.db.query(User).get(ID)
        if not U:
            return self.write( _('No such user: %s') % ID )

        self.U = U
        self.prepare_kwargs['USER'] = U


class ResourceSimpleAdd(ResourceHandler):

    title = _('Add Resource For User')
    template_path = 'admin/user/simple_resource_add.html'

    def prepare(self):

        if not self.U:
            return self.finish()

        self.form = ResourceSimpleForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.render()


    def post(self):

        form = self.form
        U = self.U

        if form.validate():

            effect_date = form.effect_date.data
            expired_date = form.expired_date.data

            for t, s in [
                ( Resource.T_CPU, form.cpu.data ),
                ( Resource.T_MEMORY, form.memory.data ),
                ( Resource.T_STORAGE, form.storage.data ),
                ( Resource.T_INSTANCE, form.instance.data ) ]:

                r = Resource( user = U, rtype = t, size = s,
                              effect_date = effect_date,
                              expired_date = expired_date )

                self.db.add(r)

            self.db.commit()

            # count be choices, email notice
            resource_mail_notice(self, U)

            url = self.reverse_url('admin:user:view')
            url += '?id=%s' % U.id
            return self.redirect( url )

        self.render()



class AllUserResourceAdd(RequestHandler):

    title = _('Add Resource For All User')
    template_path = 'admin/user/alluser_resource_add.html'

    def prepare(self):

        self.form = ResourceSimpleForm(self)
        self.prepare_kwargs['form'] = self.form


    def get(self):
        self.render()


    def post(self):

        form = self.form

        if form.validate():

            effect_date = form.effect_date.data
            expired_date = form.expired_date.data

            for U in self.db.query(User):
                if U.resources: continue # hacker
                logging.warn('add resource for %s:%s' % (U.id, U.username))
                for t, s in [
                    ( Resource.T_CPU, form.cpu.data ),
                    ( Resource.T_MEMORY, form.memory.data ),
                    ( Resource.T_STORAGE, form.storage.data ),
                    ( Resource.T_INSTANCE, form.instance.data ) ]:

                    r = Resource( user = U, rtype = t, size = s,
                                  effect_date = effect_date,
                                  expired_date = expired_date )

                    self.db.add(r)

                self.db.commit()

                # count be choices, email notice
                resource_mail_notice(self, U)


            url = self.reverse_url('admin:user')
            return self.redirect( url )

        self.render()



class UserDelete(RequestHandler):

    @has_permission('admin')
    def get(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.write( _('Give user id please.') )

        U = self.db.query(User).get( ID )
        if not U:
            return self.write( _('Can not find user %s') % ID )

#        # delete user
#
#        # 1. delete jobs
#        for j in U.jobs:
#            self.db.delete(j)
#
#        # 2. delete instances
#        for i in U.instances:
#            i.user_id = None
#
#        # 3. delete appliances:
#        for a in U.appliances:
#            a.user_id = None

        profile = self.db.query(UserProfile).filter_by(
            user_id = U.id).first()
        if profile:
            self.db.delete(profile)
            self.db.commit()

        self.db.delete( U )
        self.db.commit()

        url = self.reverse_url('admin:user')
        self.redirect_next( url )


