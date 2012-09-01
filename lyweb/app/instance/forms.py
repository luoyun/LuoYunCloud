from lyforms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.ext.sqlalchemy.fields import QuerySelectField

from wtforms.validators import ValidationError, NumberRange

import settings

from app.instance.models import Instance


class CreateInstanceBaseForm(Form):

    name = TextField( _('Name'), [validators.Length(min=2, max=30)] )
    cpus = IntegerField( _('CPU'), [NumberRange( min = 1 )], default = 1 )
    memory = IntegerField( _('Memory(M)'), [NumberRange( min = 64 )], default = 256 )
    isprivate = BooleanField( _('Hide'), default = True )


class CreateInstanceForm(CreateInstanceBaseForm):

    appliance = QuerySelectField( _('Appliance'), get_label='name' )


class BaseinfoForm(Form):

    name = TextField( _('Name'), [ validators.Length(min=3, max=120) ] )
    summary = TextField( _('Summary') )
    description = TextAreaField( _('Description') )


class ResourceForm(Form):

    cpus = IntegerField( _('CPU'), [NumberRange( min = 1, max = 2)], default = 1 )
    memory = IntegerField( _('Memory(M)'), [NumberRange( min = 64, max = 1024 )], default = 256 )


NetworkType=[
    ('default', _('Default')),
#    ('bridge', _('Bridge')),
#    ('nat', _('Nat'))
]


class NetworkForm(Form):

    type = SelectField( _('Type'), choices=NetworkType )
    ip = SelectField( _('IP') )
    netmask = TextField( _('Netmask') )
    gateway = TextField( _('Gateway') )


StorageType=[
    ('disk', _('Virtual disk')),
]

if hasattr(settings, 'MAX_STORAGE_SIZE'):
    MAX_STORAGE_SIZE = settings.MAX_STORAGE_SIZE
else:
    MAX_STORAGE_SIZE = 60 # G
class StorageForm(Form):

    type = SelectField( _('Type'), choices=StorageType )
    size = IntegerField( _('Size (GB)'), [NumberRange( min = 1, max = MAX_STORAGE_SIZE )] )


class PasswordForm(Form):

    password = PasswordField( _('Password'), [ validators.Length(min=6, max=32) ] )
    password2 = PasswordField( _('Confirm'), [ validators.Length(min=6, max=32) ] )


class PublicKeyForm(Form):

    key = TextAreaField( _('SSH Public Key') )


