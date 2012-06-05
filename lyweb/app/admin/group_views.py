# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.admin.forms import CreateGroupForm, EditGroupForm, \
    GroupAddUsersForm, GroupAddPermissionsForm

from lycustom import has_permission


class GroupManagement(LyRequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.group = None
        self.action = self.get_argument('action', 'index')

        group_id = self.get_argument('id', 0)
        if group_id:
            self.group = self.db2.query(Group).get( group_id  )
            if not self.group:
                self.write( _('No such group : %s') % group_id )
                return self.finish()


    def get(self):

        if self.action == 'index':
            self.get_index()

        elif self.action == 'view':
            self.get_view()

        elif self.action == 'add':
            self.get_add()

        elif self.action == 'edit':
            self.get_edit()

        elif self.action == 'delete':
            self.get_delete()

        elif self.action == 'users':
            self.get_users()

        elif self.action == 'permissions':
            self.get_permissions()

        elif self.action == 'add_users':
            self.get_add_users()

        elif self.action == 'add_permissions':
            self.get_add_permissions()

        else:
            self.write( _('Wrong action value!') )


    def post(self):

        if not self.action:
            self.write( _('No action found !') )

        elif self.action == 'add':
            self.post_add()

        elif self.action == 'edit':
            self.post_edit()

        elif self.action == 'add_users':
            self.post_add_users()

        elif self.action == 'add_permissions':
            self.post_add_permissions()

        else:
            self.write( _('Wrong action value!') )


    def get_index(self):

        GROUP_LIST = self.db2.query(Group).all()
        self.render( 'admin/group/index.html', title = _('Group Management'),
                     GROUP_LIST = GROUP_LIST )


    def get_view(self):

        self.render( 'admin/group/view.html', title = _('Group %s') % self.group.name,
                     group = self.group )


    # Create a new group
    def get_add(self):
        self.render( 'admin/group/add.html', title = _('Create New Group'),
                     form = CreateGroupForm() )

    def post_add(self):

        form = CreateGroupForm(self.request.arguments)

        if form.validate():

            group = self.db2.query(Group).filter_by( name=form.name.data ).all()
            if group:
                form.name.errors.append( _('This name is occupied') )
            else:
                newgroup = Group( name = form.name.data )
                self.db2.add(newgroup)
                self.db2.commit()

                url = self.application.reverse_url('admin:group')
                url += '?id=%s&action=view' % newgroup.id
                return self.redirect( url )

        # Have a error
        self.render( 'admin/group/add.html', form = form, group = self.group )


    # Edit a exist group
    def get_edit(self):
        form = EditGroupForm()
        form.name.data = self.group.name
        self.render( 'admin/group/edit.html', title = _('Edit Group %s') % self.group.name,
                     group = self.group, form = form )

    def post_edit(self):

        form = EditGroupForm(self.request.arguments)

        if form.validate():

            self.group.name = form.name.data
            self.db2.commit()

            url = self.application.reverse_url('admin:group')
            url += '?id=%s&action=view' % self.group.id
            return self.redirect( url )

        # Have a error
        self.render( 'admin/group/edit.html', form = form, group = self.group )


    # Delete a group
    def get_delete(self):
        print 'self.group.users = ', self.group.users
        print 'self.group.permissions = ', self.group.permissions
        url = self.application.reverse_url('admin:group')
        return self.redirect( url )

    # User list in group
    def get_users(self):
        self.render( 'admin/group/users.html', group = self.group )

    # Permission list in group
    def get_permissions(self):
        self.render( 'admin/group/permissions.html', group = self.group )


    # Add a user to group
    def get_add_users(self):

        self.render( 'admin/group/add_users.html', group = self.group,
                     form = GroupAddUsersForm() )


    def post_add_users(self):

        form = GroupAddUsersForm(self.request.arguments)

        if form.validate():

            exist_users = []
            unknown_users = []

            for username in form.userlist.data.split():
                user = self.db2.query(User).filter_by(username=username).first()
                if user:
                    if user not in self.group.users:
                        self.group.users.append(user)
                    else:
                        exist_users.append(username)
                else:
                    unknown_users.append(username)

            self.db2.commit()

            # TODO: exist_users have a warning ?

            if not unknown_users:
                url = self.application.reverse_url('admin:group')
                url += '?id=%s&action=view' % self.group.id
                return self.redirect( url )

            form.userlist.data = '\n'.join(unknown_users)
            form.userlist.errors.append( _('Above users are not exist in system') )


        self.render( 'admin/group/add_users.html', group = self.group,
                     form = form )


    # Add a user to group
    def get_add_permissions(self):

        choices = []
        default = []

        perms = self.db2.query(Permission).all()
        for perm in perms:
            choices.append( (perm.codename, perm.name) )

        for perm in self.group.permissions:
            default.append( perm.codename )

        form = GroupAddPermissionsForm()
        form.perms.choices = choices
        form.perms.default = default

        self.render( 'admin/group/add_permissions.html', group = self.group,
                     form = form )


    def post_add_permissions(self):

        # TODO: how use wtforms here ?
        # TODO: why self.get_argument('perms', []) does not work here ?
        perms = self.request.arguments['perms']
        for codename in perms:
            perm = self.db2.query(Permission).filter_by(codename=codename).first()
            print '[DD] codename = ', codename
            print '[DD] perm = ', perm
            if perm not in self.group.permissions:

                self.group.permissions.append(perm)

        self.db2.commit()
        url = self.application.reverse_url('admin:group')
        url += '?id=%s&action=permissions' % self.group.id
        return self.redirect( url )
