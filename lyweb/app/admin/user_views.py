# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, UserProfile
from app.instance.models import Instance

from app.account.forms import ResetPasswordForm
from app.admin.forms import CreateUserForm, UserResourceForm

import random, time, pickle, base64
from hashlib import md5, sha512, sha1
from app.account.utils import encrypt_password, check_password

from lycustom import has_permission


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
            self.get_index()

        elif self.action == 'view':
            self.get_view()

        elif self.action == 'reset_password':
            self.get_reset_password()

        elif self.action == 'add':
            self.get_add()

        elif self.action == 'instances':
            self.get_instances()

        elif self.action == 'permissions':
            self.get_permissions()

        elif self.action == 'groups':
            self.get_groups()

        elif self.action == 'edit_resources':
            self.get_edit_resources()

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

        else:
            self.write( _('Wrong action value!') )


    def get_index(self):

        # Show admin user index
        USER_LIST = self.db2.query(User).order_by('id')
        self.render('admin/user/index.html', title=_('User Management'),
                    USER_LIST = USER_LIST )


    def get_view(self):

        instances = self.db2.query(Instance).filter_by(user_id=self.user.id)

        self.render( 'admin/user/view.html',
                     title = 'View User', user = self.user,
                     INSTANCE_LIST = instances )



    def get_reset_password(self):

        self.render( 'admin/user/reset_password.html', title = _('Reset Password'),
                     form = ResetPasswordForm(), user = self.user )


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
                     form = form, user = self.user )


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


    # Get instances list of user
    def get_instances(self):

        instances = self.db2.query(Instance).filter_by(user_id=self.user.id)

        self.render( 'admin/user/instances.html',
                     title = _("User's Instances"), user = self.user,
                     INSTANCE_LIST = instances )


    # Get permissions list of user
    def get_permissions(self):

        self.render( 'admin/user/permissions.html',
                     title = _("User's Permissions"),
                     user = self.user )


    # Get group list of user
    def get_groups(self):

        self.render( 'admin/user/groups.html',
                     title = _("User's groups"),
                     user = self.user )


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

        self.render( 'admin/user/edit_resources.html',
                     title = _('Edit User %s') % self.user.username,
                     form = form, USER = self.user )
    

    def post_edit_resources(self):

        form = UserResourceForm(self.request.arguments)

        if form.validate():

            self.user.profile.memory = form.memory.data
            self.user.profile.cpus = form.cpus.data
            self.user.profile.instances = form.instances.data
            self.db2.commit()

            url = self.application.reverse_url('admin:user')
            url += '?id=%s&action=view' % self.user.id
            return self.redirect( url )

        # Have a error
        self.render( 'admin/user/edit_resources.html', form = form, USER = self.user )
