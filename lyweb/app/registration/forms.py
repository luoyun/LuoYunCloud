from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, FileField, HiddenField

from wtforms.validators import ValidationError



def my_password_confirm(form, field):
    if field.data != form.password.data:
        raise ValidationError( _('Password confirm failed') )


class RegistrationApplyForm(Form):

    email = TextField( _('Email Address'), [
            validators.Length(min=6, max=35), validators.Email()] )

    accept_rules = BooleanField( _('Registration Policy'), [
            validators.Required()] )


class RegistrationForm(Form):

    #key = HiddenField( _('Key') )

    username = TextField( _('Username'), [
            validators.Length(min=2, max=21)] )

    password = PasswordField( _('Password'), [
            validators.Length(min=6, max=120) ] )

    password_confirm = PasswordField( _('Confirm Password'), [
            my_password_confirm ] )

