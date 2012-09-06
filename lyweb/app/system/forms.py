from lyforms import Form
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


class NetworkPoolForm(Form):

    start = TextField( _('Start IP'), [ ipcheck ] )
    end = TextField( _('End IP'), [ ipcheck ] )
    netmask = TextField( _('Netmask'), [ ipcheck ] )
    gateway = TextField( _('Gateway'), [ ipcheck ] )
    nameservers = TextAreaField( _('Nameservers'), [ multi_ipcheck ] )
    exclude_ips = TextAreaField( _('Exclude ip list'), [ multi_ipcheck ] )


class DomainForm(Form):

    # TODO: make sure it's a valid domain
    topdomain = TextField( _('Top domain'), [ validators.Length(min=6, max=120) ] )
    prefix = TextField( _('Name prefix') )
    suffix = TextField( _('Name suffix') )


class NginxForm(Form):

    # TODO: make sure it's exist
    confdir = TextField( _('Config dir'), [ validators.Length(min=6, max=120) ] )
    logdir = TextField( _('Log dir'), [ validators.Length(min=6, max=120) ] )
    binpath = TextField( _('Nginx program'), [ validators.Length(min=6, max=120) ] )

class RegistrationProtocolForm(Form):

    # TODO: make sure it's exist
    text = TextAreaField( _('Registration Protocol'), [ validators.Length(min=6, max=12000) ] )


class WelcomeNewUserForm(Form):

    # TODO: make sure it's exist
    text = TextAreaField( _('Welcome New User'), [ validators.Length(min=6, max=12000) ] )

