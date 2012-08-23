# coding: utf-8

import logging, datetime, time, re
from lycustom import LyRequestHandler,  Pagination
from tornado.web import authenticated, asynchronous

from app.account.models import User, Group, Permission
from app.admin.forms import GroupForm

from lycustom import has_permission
from settings import ADMIN_USER_LIST_PAGE_SIZE as USER_PS

from sqlalchemy.sql.expression import asc, desc



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
            if self.group:
                self.render( 'admin/group/view.html',
                             title = _('View Group %s') % self.group.name,
                             GROUP = self.group )
            else:
                self.get_index()

        elif self.action == 'add':
            self.get_add()

        elif self.action == 'edit':
            self.get_edit()

        elif self.action == 'delete':
            self.get_delete()

        elif self.action == 'users':
            self.get_users()

        else:
            self.write( _('Wrong action value!') )


    def post(self):

        if not self.action:
            self.write( _('No action found !') )

        elif self.action == 'add':
            self.post_add()

        elif self.action == 'edit':
            self.post_edit()

        else:
            self.write( _('Wrong action value!') )


    def get_index(self):

        GROUP_LIST = self.db2.query(Group).order_by('id').all()
        self.render( 'admin/group/index.html',
                     title = _('Group Management'),
                     GROUP_LIST = GROUP_LIST )

    # Create a new group
    def get_add(self):
        self.render( 'admin/group/add.html', title = _('Create New Group'),
                     form = GroupForm() )

    def post_add(self):

        form = GroupForm(self.request.arguments)

        if form.validate():

            group = self.db2.query(Group).filter_by( name=form.name.data ).all()
            if group:
                form.name.errors.append( _('This name is occupied') )

            else:
                newgroup = Group(
                    name = form.name.data,
                    description = form.description.data )

                self.db2.add(newgroup)
                self.db2.commit()

                url = self.application.reverse_url('admin:group')
                return self.redirect( url )

        # Have a error
        self.render( 'admin/group/add.html', form = form, group = self.group )


    # Edit a exist group
    def get_edit(self):

        perm_choices = []
        perm_default = []

        for P in self.db2.query(Permission).all():
            perm_choices.append( (P.codename, P.name) )
            if P in self.group.permissions:
                perm_default.append( P.codename )

        form = GroupForm()
        form.perms.choices = perm_choices
        form.perms.default = perm_default
        form.process()
        form.name.data = self.group.name
        form.description.data = self.group.description


        self.render( 'admin/group/edit.html',
                     title = _('Edit Group %s') % self.group.name,
                     GROUP = self.group, form = form )


    def post_edit(self):

        perm_choices = []
        for P in self.db2.query(Permission).all():
            perm_choices.append( (P.codename, P.name) )

        form = GroupForm( self.request.arguments )
        form.perms.choices = perm_choices

        if form.validate():

            self.group.name = form.name.data
            self.group.description = form.description.data
            for codename in form.perms.data:
                P = self.db2.query(Permission).filter_by(
                    codename = codename ).first()
                self.group.permissions.append(P)
            print 'self.group.permissions = ', self.group.permissions

            self.db2.commit()

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
            self.db2.delete( self.group )
            self.db2.commit()
            url = self.reverse_url('admin:group')
            self.redirect( url )



    def get_users(self):

        page_size = int( self.get_argument('sepa', USER_PS) )
        cur_page = int( self.get_argument('p', 1) )
        by = self.get_argument('by', 'id')
        sort = self.get_argument('sort', 'ASC')

        by_exp = desc(by) if sort == 'DESC' else asc(by)
        start = (cur_page - 1) * page_size
        stop = start + page_size

        UL = self.db2.query(User).filter(
            User.groups.contains(self.group) )#.order_by( by_exp )

        print 'UL = ', UL

        total = UL.count()
        UL = UL.slice(start, stop)

        pagination = Pagination(
            total = total, page_size = page_size,
            cur_page = cur_page )

        page_html = pagination.html( self.get_page_url )
            

        d = { 'title': _('Admin User Management'),
              'USER_LIST': UL, 'PAGE_HTML': page_html,
              'TOTAL_USER': total }

        self.render( 'admin/group/users.html', GROUP = self.group,
                     USER_LIST = UL )

