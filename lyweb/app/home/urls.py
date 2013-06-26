from tornado.web import url
from . import views

handlers = [

    # Home
    ( r'/', views.Index ),
    url( r'/setlocale', views.SetLocale ),
    url( r'/no_permission', views.NoPermission ),
    url( r'/no_resource', views.NoResource ),
    url( r'/registration_protocol', views.RegistrationProtocol,
         name="registration_protocol" ),
    url( r'/welcome_new_user', views.WelcomeNewUser,
         name="welcome_new_user" ),

    url( r'/ly/upload/kindeditor', views.UploadKindeditor,
         name="upload:kindeditor" ),

]
