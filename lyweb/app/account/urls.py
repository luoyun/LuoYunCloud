from tornado.web import url
from . import views
from . import user_views as user
from . import admin_views as admin

handlers = [

    ( r'/login', views.Login ),
    ( r'/logout', views.Logout ),

    ( r'/openid/qq/login', views.QQLogin ),
    url ( r'/openid/user/binding', views.OpenIDUserBinding,
          name="openid:user:binding" ),
    url ( r'/openid/user/new', views.OpenIDUserNew,
          name="openid:user:new" ),

    url( r'/account', views.MyAccount, name='account'),

    # email validate
    url( r'/account/email/validate', views.EmailValidate,
         name='account:email:validate'),

    # password reset
    url( r'/account/resetpass_apply', views.ResetPassApply,
         name='account:resetpass_apply'),

    url( r'/account/resetpass', views.ResetPass,
         name='account:resetpass'),

    url( r'/account/resetmypass', views.ResetMyPass,
         name='account:reset_mypass'),

    # baseinfo
    url( r'/account/baseinfo/edit', views.BaseInfoEdit,
         name='account:baseinfo:edit'),

    # avatar
    url( r'/account/avatar/edit', views.AvatarEdit,
         name='account:avatar:edit'),

    # pulic key
    url( r'/account/public_key', views.PublicKeyIndex,
         name='account:public_key' ),

    url( r'/account/public_key/add', views.PublicKeyAdd,
         name='account:public_key:add' ),

    url( r'/account/public_key/edit', views.PublicKeyEdit,
         name='account:public_key:edit' ),

    url( r'/account/public_key/delete', views.PublicKeyDelete,
         name='account:public_key:delete' ),

    # user
    url( r'/user/view', user.View, name='user:view' ),


    # admin
    url(r'/admin/account/mailto', admin.MailTo,
        name='admin:account:mailto'),

]
