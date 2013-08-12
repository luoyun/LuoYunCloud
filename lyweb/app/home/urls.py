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

    url( r'/t/preview', views.Preview, name='preview' ),
    url( r'/search', views.Search, name='search' ),
]
