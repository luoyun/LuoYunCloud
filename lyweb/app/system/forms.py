from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.ext.sqlalchemy.fields import QuerySelectField

from wtforms.validators import ValidationError, NumberRange

import settings

import IPy


def ipcheck(form, field):
    try:
        IPy.parseAddress(field.data)
    except ValueError, msg:
        # msg is "single byte must be 0 <= byte < 256"
        raise ValidationError(msg)


def multi_ipcheck(form, field):
    error = []
    for x in field.data.split():
        try:
            IPy.parseAddress(x)
        except ValueError:
            error.append( x )

    if error:
        raise ValidationError( _('Error IP: %s') % error )


class BaseinfoForm(Form):

    # TODO: Important ! make sure directory is exists !
    app_dir = TextField( _('Save directory') )
    app_url = TextField( _('Download url prefix') )
    admin_email = TextField( _('Admin email') )


class CLCForm(Form):

    ip = TextField( _("IP"), [ ipcheck ] )
    port = TextField( _("Port") )


class DBForm(Form):

    dbhost = TextField( _('server') )
    dbtype = TextField( _('engine') )
    dbuser = TextField( _('username') )
    dbpass = TextField( _('password') )
    dbname = TextField( _('db name') )


class NameserversForm(Form):

    nameservers = TextAreaField( _('Nameservers'), [ multi_ipcheck ] )


class NginxForm(Form):

    conf_path = TextField( _('Config dir') )
    log_path  = TextField( _('Log dir') )
    nginx     = TextField( _('Nginx program') )
    template  = TextAreaField( _('Nginx Template') )


class RegistrationProtocolForm(Form):

    # TODO: make sure it's exist
    text = TextAreaField( _('Registration Protocol'), [ validators.Length(min=6, max=12000) ] )


class WelcomeNewUserForm(Form):

    # TODO: make sure it's exist
    text = TextAreaField( _('Welcome New User'), [ validators.Length(min=6, max=12000) ] )


class QQAuth2Form(Form):

    app_id  = TextField( 'APP ID' )
    app_key = TextField( 'APP KEY' )
    redirect_uri = TextField( 'Redirect URI' )
    enabled = BooleanField( 'Is Enabled ?', default = False )

