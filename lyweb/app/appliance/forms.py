from lyforms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.validators import ValidationError



class EditApplianceForm(Form):

    name = TextField( _('Name') )
    summary = TextField( _('Summary') )
    catalog = SelectField( _('Catalog') )
    logo = FileField( _('Logo') )
    description = TextAreaField( _('Description') )


