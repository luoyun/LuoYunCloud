from lyforms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField

from wtforms.validators import ValidationError


def password_confirm(form, field):
    if field.data != form.password_confirm.data:
        raise ValidationError('password confirm failed')


class CreateUserForm(Form):
    username         = TextField( _('Username'), [validators.Length(min=4, max=25)] )
    email            = TextField( _('Email Address'), [validators.Length(min=6, max=35), validators.Email()] )
    password         = PasswordField( _('Password'),
                                      [ password_confirm, validators.Length(min=6, max=120) ] )
    password_confirm = PasswordField( _('Confirm Password') )

class UserResourceForm(Form):
    memory = IntegerField( _('Memory(M)'), [validators.NumberRange(min=256, max=10240)])
    cpus = IntegerField( _('CPUs'), [validators.NumberRange(min=1, max=20)])
    instances = IntegerField( _('Instances'), [validators.NumberRange(min=1, max=100)])
    storage = IntegerField( _('Storage(G)'), [validators.NumberRange(min=2, max=100)])


class GroupForm(Form):
    name = TextField( _('Name'), [validators.Length(min=2, max=25)] )
    description = TextAreaField( _('Description') )
    perms = SelectMultipleField( _('Permissions') )


# Support wiki catalog and appliance catalog
class CatalogForm(Form):

    name = TextField( _('Name'), [validators.Length(min=2, max=32)] )
    summary = TextField( _('Summary'), [validators.Length(min=2, max=256)] )
    description = TextAreaField( _('Description') )


class UserGroupEditForm(Form):
    groups = SelectMultipleField( _('Groups') )
