from lyforms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, FileField

from wtforms.validators import ValidationError


def password_confirm(form, field):
    if field.data != form.password_confirm.data:
        raise ValidationError( _('password confirm failed') )



class LoginForm(Form):
    username = TextField( _('Username') )
    password = PasswordField( _('Password') )


class ResetPasswordForm(Form):
    password = PasswordField(
        _('Password'), [ password_confirm, validators.Length(min=6, max=120) ] )
    password_confirm = PasswordField( _('Confirm Password') )


class ResetPasswordApplyForm(Form):
    email = TextField( _('Email Address'), [validators.Length(min=6, max=35), validators.Email()])


class RegistrationForm(ResetPasswordForm):
    username     = TextField( _('Username'), [validators.Length(min=4, max=25)])
    email        = TextField( _('Email Address'), [validators.Length(min=6, max=35), validators.Email()])
    accept_rules = BooleanField( _('Registration Rules'), [validators.Required()])



class ProfileForm(Form):
    birthday  = DateTimeField('Your Birthday', format='%m/%d/%y')
    signature = TextAreaField('Forum Signature')

class AdminProfileForm(ProfileForm):
    username = TextField('Username', [validators.Length(max=40)])
    level    = IntegerField('User Level', [validators.NumberRange(min=0, max=10)])


class AvatarEditForm(Form):

    avatar = FileField( _('Logo') )

