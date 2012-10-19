from tornado.web import url
import app.home.views as home

handlers = [

    # Home
    url( r'/i18n/setlang', home.SetLocale ),
    url( r'/no_permission', home.NoPermission ),
    url( r'/no_resource', home.NoResource ),
    url( r'/registration_protocol', home.RegistrationProtocol,
         name="registration_protocol" ),
    url( r'/welcome_new_user', home.WelcomeNewUser,
         name="welcome_new_user" ),

    url( r'/ly/upload/kindeditor', home.UploadKindeditor,
         name="upload:kindeditor" ),

]
