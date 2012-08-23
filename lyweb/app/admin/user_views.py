# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, UserProfile
from app.instance.models import Instance

from app.account.forms import ResetPasswordForm
from app.admin.forms import CreateUserForm, UserResourceForm, \
    UserGroupEditForm

import random, time, pickle, base64
from hashlib import md5, sha512, sha1
from app.account.utils import encrypt_password, check_password

from sqlalchemy.sql.expression import asc, desc

from lycustom import has_permission

from settings import ADMIN_USER_LIST_PAGE_SIZE as USER_PS


class UserManagement(LyRequestHandler):

    ''' I want to build a large views , :-) '''


    @has_permission('admin')
    def prepare(self):

        self.user = None
        self.action = self.get_argument('action', 'index')

        user_id = self.get_argument('id', 0)
        if user_id:
            self.user = self.db2.query(User).get( user_id  )
            if not self.user:
                self.write( _('No such user : %s') % user_id )
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

        else:
            self.write( _('Wrong action value!') )


    def post(self):

        if not self.action:
            self.write( _('No action found !') )

        elif self.action == 'reset_password':
            self.post_reset_password()

        elif self.action == 'add':
            self.post_add()

        elif self.action == 'edit_resources':
            self.post_edit_resources()

        elif self.action == 'edit_groups':
            self.post_edit_groups()

        else:
            self.write( _('Wrong action value!') )


    def get_index(self):

        page_size = int( self.get_argument('sepa', USER_PS) )
        cur_page = int( self.get_argument('p', 1) )
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')
        gid = (self.get_argument('gid', 0))


        if by == 'date_joined':
            by = User.date_joined
        elif by == 'last_login':
            by = User.last_login
        else:
            by = User.id

        by_exp = desc(by) if sort == 'DESC' else asc(by)

        start = (cur_page - 1) * page_size
        stop = start + page_size

        UL = self.db2.query(User)

        GROUP = self.db2.query(Group).get(gid)
        if GROUP:
            UL = UL.filter( User.groups.contains(GROUP) )

        UL = UL.order_by( by_exp )

        total = UL.count()
        UL = UL.slice(start, stop)

        pagination = Pagination(
            total = total, page_size = page_size,
            cur_page = cur_page )

        page_html = pagination.html( self.get_page_url )
            

        d = { 'title': _('Admin User Management'),
              'USER_LIST': UL, 'PAGE_HTML': page_html,
              'TOTAL_USER': total,
              'GROUP': GROUP }

        self.render( 'admin/user/index.html', **d )


    def get_view(self):

        self.render( 'admin/user/view.html',
                     title = 'View User', user = self.user )



    def get_reset_password(self):

        self.render( 'admin/user/reset_password.html', title = _('Reset Password'),
                     form = ResetPasswordForm(), USER = self.user )


    def post_reset_password(self):

        form = ResetPasswordForm(self.request.arguments)

        if form.validate():

            salt = md5(str(random.random())).hexdigest()[:12]
            hsh = encrypt_password(salt, form.password.data)
            enc_password = "%s$%s" % (salt, hsh)

            self.user.password = enc_password
            self.db2.commit()

            url = self.application.reverse_url('admin:user')
            url += '?id=%s&action=view' % self.user.id
            return self.redirect( url )

        self.render( 'admin/user/reset_password.html', title = _('Reset Password'),
                     form = form, USER = self.user )


    # Add a new user manually
    def get_add(self):

        self.render( 'admin/user/add.html', title = _('Creat New User'),
                     form = CreateUserForm() )
    

    def post_add(self):

        form = CreateUserForm(self.request.arguments)

        if form.validate():

            user = self.db2.query(User).filter_by( username=form.username.data ).all()
            if user:
                form.username.errors.append( _('This username is occupied') )
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

        form = UserResourceForm()
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
                     title = _('Edit User %s') % self.user.username,
                     form = form, USER = self.user )
    


    def post_edit_resources(self):

        form = UserResourceForm(self.request.arguments)

        if form.validate():

            self.user.profile.memory = form.memory.data
            self.user.profile.cpus = form.cpus.data
            self.user.profile.instances = form.instances.data
            self.user.profile.storage = form.storage.data
            self.db2.commit()

            url = self.application.reverse_url('admin:user')
            url += '?id=%s&action=view' % self.user.id
            return self.redirect( url )

        # Have a error
        self.render( 'admin/user/edit_resources.html', form = form, USER = self.user )


    def get_set_lock_flag(self):

        flag = self.get_argument('islocked', None)
        self.user.islocked = True if flag == 'true' else False
        self.db2.commit()

        url = self.reverse_url('admin:user')
        url += '?id=%s&action=view' % self.user.id

        self.redirect( url )

    def get_edit_groups(self):

        choices = []
        default = []

        groups = self.db2.query(Group).all()
        for G in groups:
            choices.append( (G.name, G.name) )
            if G in self.user.groups:
                default.append( G.name )

        form = UserGroupEditForm()
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
