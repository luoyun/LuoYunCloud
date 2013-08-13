from tornado.web import url
import app.admin.views as admin
import app.admin.user_views as user
import app.admin.group_views as group
import app.admin.permission_views as permission
import app.admin.appliance_views as appliance
import app.admin.instance_views as instance
import app.admin.node_views as node
import app.admin.job_views as job



handlers = [

    # Admin
    url(r'/admin', admin.Index, name='admin:index'),

    url(r'/admin/account', admin.AccountIndex, name='admin:account'),

    # User
    url(r'/admin/user', user.Index, name='admin:user'),

    url(r'/admin/user/add', user.UserAdd, name='admin:user:add'),

    url(r'/admin/user/delete', user.UserDelete, name='admin:user:delete'),

    url(r'/admin/user/view', user.View, name='admin:user:view'),

    url(r'/admin/user/resetpass', user.ResetPass,
        name='admin:user:resetpass'),

    url(r'/admin/user/group/edit', user.GroupEdit,
        name='admin:user:group:edit'),

    url(r'/admin/user/resource/add', user.ResourceAdd,
        name='admin:user:resource:add'),

    url(r'/admin/user/resource/simple_add', user.ResourceSimpleAdd,
        name='admin:user:resource:simple_add'),

    url(r'/admin/user/resource/all_add', user.AllUserResourceAdd,
        name='admin:user:resource:all_add'),

    # Group
    url(r'/admin/group', group.GroupManagement, name='admin:group'),
    url(r'/admin/permission', permission.PermissionManagement, name='admin:permission'),

    # Appliance
    url( r'/admin/appliance', appliance.Index,
         name='admin:appliance' ),

    url( r'/admin/appliance/view', appliance.ApplianceView,
         name='admin:appliance:view' ),

    url( r'/admin/appliance/edit', appliance.ApplianceEdit,
         name='admin:appliance:edit' ),

    url( r'/admin/appliance/change_user',
         appliance.ApplianceChangeUser,
         name='admin:appliance:change_user' ),

    url( r'/admin/appliance/catalog', appliance.CatalogIndex,
         name='admin:appliance:catalog' ),

    url( r'/admin/appliance/catalog/view', appliance.CatalogView,
         name='admin:appliance:catalog:view' ),

    url( r'/admin/appliance/catalog/add', appliance.CatalogAdd,
         name='admin:appliance:catalog:add' ),

    url( r'/admin/appliance/catalog/edit', appliance.CatalogEdit,
         name='admin:appliance:catalog:edit' ),

    url( r'/admin/appliance/catalog/delete', appliance.CatalogDelete,
         name='admin:appliance:catalog:delete' ),

    url(r'/admin/node', node.NodeManagement, name='admin:node'),
    url(r'/admin/job', job.JobManagement, name='admin:job'),

    # instance
    url(r'/admin/instance', instance.Index, name='admin:instance'),
    url(r'/admin/instance/view', instance.View, name='admin:instance:view'),

]
