from tornado.web import url
from . import views as myun
from .instance import views as I
from .appliance import views as A


handlers = [

    url( r'/myun', myun.Index, name='myun:index'),

    # Instance
    url( r'/myun/instance', I.Index,  name='myun:instance'),

    url( r'/myun/instance/create', I.InstanceCreate,
         name='myun:instance:create' ),

    url( r'/myun/instance/view', I.View,
         name='myun:instance:view' ),

    url( r'/myun/instance/global_password_edit',
         I.GlobalPasswordEdit,
         name='myun:instance:global_password_edit' ),

    # Instance baseinfo
    url( r'/myun/instance/baseinfo/edit', I.BaseinfoEdit,
         name='myun:instance:baseinfo:edit' ),

    # Instance resource
    url( r'/myun/instance/resource/edit', I.ResourceEdit,
         name='myun:instance:resource:edit' ),

    # Instance storage
    url( r'/myun/instance/storage/add', I.StorageAdd,
         name='myun:instance:storage:add' ),

    url( r'/myun/instance/storage/edit', I.StorageEdit,
         name='myun:instance:storage:edit' ),

    url( r'/myun/instance/storage/delete', I.StorageDelete,
         name='myun:instance:storage:delete' ),

    # Instance network
    url( r'/myun/instance/network/add', I.NetworkAdd,
         name='myun:instance:network:add' ),

    url( r'/myun/instance/network/delete', I.NetworkDelete,
         name='myun:instance:network:delete' ),

    # Instance secret
    url( r'/myun/instance/password/edit', I.InstancePasswordEdit,
         name='myun:instance:password:edit' ),

    # Instance public key
    url( r'/myun/instance/public_key/edit', I.InstancePublicKeyEdit,
         name='myun:instance:public_key:edit' ),

    # Instance domain
    url( r'/myun/instance/domain/add', I.DomainAdd,
         name='myun:instance:domain:add' ),

    url( r'/myun/instance/domain/edit', I.DomainEdit,
         name='myun:instance:domain:edit' ),

    url( r'/myun/instance/domain/delete', I.DomainDelete,
         name='myun:instance:domain:delete' ),

    # Instance portmapping
    url( r'/myun/instance/portmapping/add', I.PortMappingAdd,
         name='myun:instance:portmapping:add' ),

    url( r'/myun/instance/portmapping/delete', I.PortMappingDelete,
         name='myun:instance:portmapping:delete' ),


    # Appliance
    url( r'/myun/appliance', A.Index,  name='myun:appliance'),
    url( r'/myun/appliance/view', A.View, name='myun:appliance:view' ),

    url( r'/myun/appliance/baseinfo/edit', A.BaseinfoEdit,
         name='myun:appliance:baseinfo:edit' ),

]
