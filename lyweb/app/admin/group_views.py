# coding: utf-8

import logging, datetime, time, re
from lycustom import RequestHandler
from tornado.web import authenticated, asynchronous

from app.auth.models import User, Group, Permission
from app.admin.forms import GroupForm, GroupSelectForm

from lycustom import has_permission
from settings import ADMIN_USER_LIST_PAGE_SIZE as USER_PS

from sqlalchemy.sql.expression import asc, desc



class GroupMerge(RequestHandler):

    template_path = 'admin/account/group_merge.html'

    @has_permission('admin')
    def prepare(self):

        ID = self.get_argument_int('id', None)
        if not ID:
            return self.finish( _('Give me group id please.') )

        G = self.db.query(Group).get( ID  )
        if not G:
            return self.finish( _('Can not find group %s') % ID )

        group_choices = []
        for g in self.db.query(Group).all():
            group_choices.append( (str(g.id), g.name) )

        form = GroupSelectForm(self)
        form.group.choices = group_choices

        self.prepare_kwargs['GROUP'] = G
        self.prepare_kwargs['form'] = form

    def get(self):
        self.render()

    def post(self):

        G = self.prepare_kwargs['GROUP']
        form = self.prepare_kwargs['form']

        if form.validate():

            new_group_id = self.get_int( form.group.data )

            from app.auth.models import user_groups
            from sqlalchemy.sql import select

            s = user_groups.update().where(
                user_groups.c.group_id == G.id).values(
                group_id = new_group_id )

            result = self.db.execute(s)

            self.db.commit()

            url = self.reverse_url('admin:group')
            return self.redirect( url )

        self.render()


class GroupManagement(RequestHandler):


    @has_permission('admin')
    def prepare(self):

        self.group = None
        self.action = self.get_argument('action', 'index')

        group_id = self.get_argument('id', 0)
        if group_id:
            self.group = self.db.query(Group).get( group_id  )
            if not self.group:
                self.write( self.trans(_('No such group : %s')) % group_id )
                return self.finish()


    def get(self):

        if self.action == 'index':
            if self.group:
                self.render( 'admin/group/view.html',
                             title = self.trans(_('View Group %s')) % self.group.name,
                             GROUP = self.group )
            else:
                self.get_index()

        elif self.action == 'add':
            self.get_add()

        elif self.action == 'edit':
            self.get_edit()

        elif self.action == 'delete':
            self.get_delete()

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def post(self):

        if not self.action:
            self.write( self.trans(_('No action found !')) )

        elif self.action == 'add':
            self.post_add()

        elif self.action == 'edit':
            self.post_edit()

        else:
            self.write( self.trans(_('Wrong action value!')) )


    def get_index(self):

        GROUP_LIST = self.db.query(Group).order_by('id').all()
        self.render( 'admin/group/index.html',
                     title = self.trans(_('Group Management')),
                     GROUP_LIST = GROUP_LIST )

    # Create a new group
    def get_add(self):
        self.render( 'admin/group/add.html', title = self.trans(_('Create New Group')),
                     form = GroupForm(self) )

    def post_add(self):

        form = GroupForm(self)

        if form.validate():

            group = self.db.query(Group).filter_by( name=form.name.data ).all()
            if group:
                form.name.errors.append( self.trans(_('This name is occupied')) )

            else:
                newgroup = Group(
                    name = form.name.data,
                    description = form.description.data )

                self.db.add(newgroup)
                self.db.commit()

                url = self.application.reverse_url('admin:group')
                return self.redirect( url )

        # Have a error
        self.render( 'admin/group/add.html', form = form, group = self.group )


    # Edit a exist group
    def get_edit(self):

        perm_choices = []
        perm_default = []

        for P in self.db.query(Permission).all():
            perm_choices.append( (P.codename, P.name) )
            if P in self.group.permissions:
                perm_default.append( P.codename )

        form = GroupForm(self)
        form.perms.choices = perm_choices
        form.perms.default = perm_default
        form.process()
        form.name.data = self.group.name
        form.description.data = self.group.description


        self.render( 'admin/group/edit.html',
                     title = self.trans(_('Edit Group %s')) % self.group.name,
                     GROUP = self.group, form = form )


    def post_edit(self):

        perm_choices = []
        for P in self.db.query(Permission).all():
            perm_choices.append( (P.codename, P.name) )

        form = GroupForm(self)
        form.perms.choices = perm_choices

        if form.validate():

            self.group.name = form.name.data
            self.group.description = form.description.data
            bak = self.group.permissions
            self.group.permissions = []
            for codename in form.perms.data:
                P = self.db.query(Permission).filter_by(
                    codename = codename ).first()
                self.group.permissions.append(P)
            #print 'self.group.permissions = ', self.group.permissions

            self.db.commit()

            url = self.application.reverse_url('admin:group')
            return self.redirect( url )

        # Have a error
        self.render( 'admin/group/edit.html',
                     form = form, GROUP = self.group )


    def get_delete(self):

        if self.group.users or self.group.islocked:
            self.render( 'admin/group/delete_failed.html',
                         GROUP = self.group )
        else:
            self.db.delete( self.group )
            self.db.commit()
            url = self.reverse_url('admin:group')
            self.redirect( url )



