from tornado.web import url
import app.account.views as account
import app.message.views as msg

handlers = [

    url( r'/login', account.Login,
         name='login'),

    url( r'/logout', account.Logout,
         name='logout'),

    url( r'/register', account.Register,
         name='register'),

    url( r'/register_apply', account.RegisterApply,
         name='register_apply'),

    url( r'/account/reset_password_apply',
         account.ResetPasswordApply, name='reset_password_apply'),

    url( r'/account/reset_password_complete',
         account.ResetPasswordComplete, name='reset_password_complete'),


    url( r'/account', account.Index,
         name='account:index'),

    url( r'/account/permission', account.MyPermission,
         name='account:permission'),

    url( r'/user/([0-9]+)', account.ViewUser,
         name='account:view'),

    url( r'/group/([0-9]+)', account.ViewGroup,
         name='account:group:view'),

    url( r'/account/reset_password', account.ResetPassword,
         name='account:reset_password'),

    url( r'/account/avatar/edit', account.AvatarEdit,
         name='account:avatar:edit'),

    url( r'/account/([0-9]+)/delete', account.Delete,
         name='account:delete'),

    url( r'/account/([0-9]+)/islocked', account.islockedToggle,
         name='account:islocked'),

]
