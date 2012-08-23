from tornado.web import url
import app.admin.views as admin
import app.admin.user_views as user
import app.admin.group_views as group
import app.admin.permission_views as permission
import app.admin.system_views as system
import app.admin.appliance_views as appliance
import app.admin.instance_views as instance
import app.admin.node_views as node
import app.admin.job_views as job
import app.admin.wiki_views as wiki

import app.appliance.views as appliance_orig

handlers = [

    # Admin
    url(r'/admin', admin.Index, name='admin:index'),

    url(r'/admin/user', user.UserManagement, name='admin:user'),
    url(r'/admin/group', group.GroupManagement, name='admin:group'),
    url(r'/admin/permission', permission.PermissionManagement, name='admin:permission'),
    url(r'/admin/system', system.SystemManagement, name='admin:system'),

    url(r'/admin/appliance', appliance.ApplianceManagement, name='admin:appliance'),
    url(r'/admin/appliance/catalog', appliance.AdminCatalog, name='admin:appliance:catalog'),

    # TODO:
    url(r'/admin/appliance/([0-9]+)/delete', appliance_orig.Delete, name='admin:appliance:delete'),

    url(r'/admin/instance', instance.InstanceManagement, name='admin:instance'),
    url(r'/admin/node', node.NodeManagement, name='admin:node'),
    url(r'/admin/job', job.JobManagement, name='admin:job'),
    url(r'/admin/wiki', wiki.WikiManagement, name='admin:wiki'),

]
