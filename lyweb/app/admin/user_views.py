# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, UserProfile, \
    UserResetpass
from app.instance.models import Instance
from app.job.models import Job

from app.account.forms import ResetPasswordForm
from app.admin.forms import CreateUserForm, UserResourceForm, \
    UserGroupEditForm

import random, time, pickle, base64
from hashlib import md5, sha512, sha1
from app.account.utils import encrypt_password, check_password

from sqlalchemy.sql.expression import asc, desc
from sqlalchemy import and_, or_

from lycustom import has_permission

from settings import ADMIN_USER_LIST_PAGE_SIZE as USER_PS
import settings

from ytool.pagination import pagination



class UserManagement(LyRequestHandler):

    ''' I want to build a large views , :-) '''


    @has_permission('admin')
    def prepare(self):

        self.user = None
        self.action = self.get_argument('action', 'index')

        user_id = self.get_argument_int('id', 0)
        if user_id:
            self.user = self.db2.query(User).get( user_id  )
            if not self.user:
                self.write( self.trans(_('No such user : %s')) % user_id )
                return self.finish()


    def get(self):

        if self.action == 'index':
            if self.user:
                self.get_view()
            else:
                self.get_index()

        elif self.action == 'view':
            self.get_view()

        elif self.action == 'reset_password':
            self.get_reset_password()

        elif self.action == 'add':
            self.get_add()

        elif self.action == 'edit_resources':
            self.get_edit_resources()

        elif self.action == 'set_lock_flag':
            self.get_set_lock_flag()

        elif self.action == 'edit_groups':
            self.get_edit_groups()

        elif self.action == 'edit_description':
            return self.render( 'admin/user/edit_description.html', USER = self.user )

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def post(self):

        if not self.action:
            self.write( self.trans(_('No action found !')) )

        elif self.action == 'reset_password':
            self.post_reset_password()

        elif self.action == 'add':
            self.post_add()

        elif self.action == 'edit_resources':
            self.post_edit_resources()

        elif self.action == 'edit_groups':
            self.post_edit_groups()

        elif self.action == 'edit_description':
            self.post_edit_description()

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def get_index(self):

        page_size = self.get_argument_int('sepa', USER_PS)
        cur_page = self.get_argument_int('p', 1)
        by = self.get_argument('by', 'id')
        order = self.get_argument_int('order', 1)
        gid = self.get_argument_int('gid', -1)
        search = self.get_argument('search', False)

        UL = self.db2.query(User)

        if by == 'id':
            by = User.id
        elif by == 'date_joined':
            by = User.date_joined
        elif by == 'last_login':
            by = User.last_login
        elif by == 'last_active':
            by = User.last_active
        elif by == 'username':
            by = User.username
        elif by == 'islocked':
            by = User.islocked
        elif by == 'description':
            by = User.id
            UL = UL.filter( User.description != None )
        else:
            by = User.id

        by_exp = desc(by) if order else asc(by)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        if search:
            search = '%' + search + '%'
            PL = self.db2.query(UserProfile).filter(
                UserProfile.email.like(search))
            user_ids = [ x.user_id for x in PL ]
            UL = UL.filter( or_(User.username.like(search),
                                User.id.in_( user_ids ) ) )

        GROUP = None
        if gid == 0:
            UL = UL.filter( ~User.groups.any() )
        elif gid > 0:
            GROUP = self.db2.query(Group).get(gid)
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
              'urlupdate': self.urlupdate,
              'USER_LIST': UL, 'PAGE_HTML': page_html,
              'TOTAL_USER': total,
              'PAGE_SIZE': page_size,
              'GROUP': GROUP, 'GID': gid,
              'GROUP_LIST': self.db2.query(Group).all()}

        if self.get_argument('ajax', None):
            self.render( 'admin/user/index.ajax', **d )
        else:
            self.render( 'admin/user/index.html', **d )


    def get_view(self):

        TAB = self.get_argument('tab', 'general')

        jobs = self.db2.query(Job).filter(
            Job.user_id == self.user.id).order_by(
            desc(Job.id) ).limit(10).all()

        d = { 'title': self.trans(_('View User')), 'TAB': TAB,
              'U': self.user, 'JOB_LIST': jobs }

        if self.get_argument('ajax', None):
            self.render( 'admin/user/view.ajax.html', **d)
        else:
            self.render( 'admin/user/view.html', **d)


    def get_reset_password(self):

        d = { 'title': self.trans(_('Reset Password For "%s"')) % self.user.username,
              'U': self.user, 'form': ResetPasswordForm(self) }
        self.render( 'admin/user/reset_password.html', **d)


    def post_reset_password(self):

        form = ResetPasswordForm(self)

        if form.validate():

            salt = md5(str(random.random())).hexdigest()[:12]
            hsh = encrypt_password(salt, form.password.data)
            enc_password = "%s$%s" % (salt, hsh)

            self.user.password = enc_password
            self.db2.commit()

            url = self.reverse_url('admin:user')
            url += '?id=%s&action=view' % self.user.id
            return self.redirect( url )

        self.render( 'admin/user/reset_password.html', title = self.trans(_('Reset Password')),
                     form = form, U = self.user )


    # Add a new user manually
    def get_add(self):

        self.render( 'admin/user/add.html', title = self.trans(_('Creat New User')),
                     form = CreateUserForm(self) )
    

    def post_add(self):

        form = CreateUserForm(self)

        if form.validate():

            user = self.db2.query(User).filter_by( username=form.username.data ).all()
            if user:
                form.username.errors.append( self.trans(_('This username is occupied')) )
            else:
                salt = md5(str(random.random())).hexdigest()[:12]
                hsh = encrypt_password(salt, form.password.data)
                enc_password = "%s$%s" % (salt, hsh)

                newuser = User( username = form.username.data,
                                password = enc_password )
                self.db2.add(newuser)
                self.db2.commit()
                # Create profile
                profile = UserProfile(newuser, email = form.email.data)
                self.db2.add(profile)
                self.db2.commit()

                url = self.application.reverse_url('admin:user')
                url += '?id=%s&action=view' % newuser.id
                return self.redirect( url )

        # Have a error
        self.render( 'admin/user/add.html', form = form )


    def get_edit_resources(self):

        form = UserResourceForm(self)
        # TODO: a temp hack
        if not self.user.profile:
            # Create profile
            from app.account.models import UserProfile
            profile = UserProfile(self.user, email = 'user%s@luoyun.co' % self.user.id)
            self.db2.add(profile)
            self.db2.commit()
        form.memory.data = self.user.profile.memory
        form.cpus.data = self.user.profile.cpus
        form.instances.data = self.user.profile.instances
        form.storage.data = self.user.profile.storage

        self.render( 'admin/user/edit_resources.html',
                     title = self.trans(_('Edit User %s')) % self.user.username,
                     form = form, USER = self.user )
    

    def post_edit_resources(self):

        form = UserResourceForm(self)

        if form.validate():

            self.user.profile.memory = form.memory.data
            self.user.profile.cpus = form.cpus.data
            self.user.profile.instances = form.instances.data
            self.user.profile.storage = form.storage.data
            self.db2.commit()

            url = self.reverse_url('admin:user')
            url += '?id=%s&action=view' % self.user.id
            return self.redirect( url )

        # Have a error
        self.render( 'admin/user/edit_resources.html', form = form, USER = self.user )


    def get_set_lock_flag(self):

        if self.current_user.id == self.user.id:
            return self.write( self.trans(_('You can not lock yourself !')) )

        flag = self.get_argument('islocked', None)
        self.user.islocked = True if flag == 'true' else False
        self.db2.commit()

        url = self.reverse_url('admin:user')
        url += '?id=%s&tab=other' % self.user.id

        self.redirect( url )


    def get_edit_groups(self):

        choices = []
        default = []

        groups = self.db2.query(Group).all()
        for G in groups:
            choices.append( (G.name, G.name) )
            if G in self.user.groups:
                default.append( G.name )

        form = UserGroupEditForm(self)
        form.groups.choices = choices
        form.groups.default = default
        form.process()

        self.render( 'admin/user/edit_groups.html',
                     form = form, USER = self.user )


    def post_edit_groups(self):

        groups = self.request.arguments.get('groups', [])
        group_obj = []

        for name in groups:
            G = self.db2.query(Group).filter_by(name=name).first()
            if G: group_obj.append( G )

        self.user.groups = group_obj
        self.db2.commit()

        url = self.reverse_url('admin:user')
        url += '?id=%s' % self.user.id
        return self.redirect( url )

    def post_edit_description(self):
        print 'self.request ', self.request
        description = self.get_argument('description', '').strip()
        if self.user:
            self.user.description = description if description else None
            self.db2.commit()

        url = '%s?id=%s' % (self.reverse_url('admin:user'), self.user.id)
        return self.redirect( url )
        


class ResetpassApply(LyRequestHandler):

    @has_permission('admin')
    def get(self):

        applys = self.db2.query(UserResetpass).all()

        self.render( 'admin/user/reset_password_history.html',
                     APPLY_LIST = applys )
