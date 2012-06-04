from lyforms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.ext.sqlalchemy.fields import QuerySelectField

from wtforms.validators import ValidationError, NumberRange



class CreateInstanceBaseForm(Form):

    name = TextField( _('Name'), [ validators.Length(min=3, max=120) ] )
    #summary = TextField( _('Summary') )
    cpus = IntegerField( _('CPU'), [NumberRange( min = 1, max = 2)], default = 1 )
    memory = IntegerField( _('Memory'), [NumberRange( min = 64, max = 1024 )], default = 256 )

class CreateInstanceForm(CreateInstanceBaseForm):

    appliance = QuerySelectField( _('Appliance'), get_label='name' )


