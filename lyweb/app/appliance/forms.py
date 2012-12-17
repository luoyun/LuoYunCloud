from lyforms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.validators import ValidationError


from app.appliance.models import OSType

_new_OSType = [(str(x), y) for x, y in OSType]

class EditApplianceForm(Form):

    name = TextField( _('Name'), [validators.Length(min=2, max=64)] )
    os = SelectField( _('OS'), choices=_new_OSType )
    summary = TextField( _('Summary') )
    catalog = SelectField( _('Catalog') )
    logo = FileField( _('Logo') )
    description = TextAreaField( _('Description') )


