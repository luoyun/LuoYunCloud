from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, FileField, SelectField

from wtforms.validators import ValidationError


def my_password_confirm(form, field):
    if field.data != form.password.data:
        raise ValidationError( _('Password confirm failed') )


from app.auth.models import User
from app.auth.utils import check_login_passwd

class LoginForm(Form):

    user = TextField( _('User') )
    password = PasswordField( _('Password') )

    def validate_user(form, field):
        if '@' in field.data:
            user = form._handler.db.query(User).filter_by(
                email = field.data ).first()
        else:
            user = form._handler.db.query(User).filter_by(
                username = field.data ).first()

        if not user:
            raise ValidationError( _('User does not exist.') )

        if user.is_locked:
            raise ValidationError( _('You have been locked.') )

        form.__dict__['true_user'] = user

    def validate_password(form, field):

        if '@' in form.user.data:
            user = form._handler.db.query(User).filter_by(
                email = form.user.data ).first()
        else:
            user = form._handler.db.query(User).filter_by(
                username = form.user.data ).first()

        if user:
            if not check_login_passwd( field.data,
                                       user.password ):
                raise ValidationError( _('Password is wrong.') )





class ResetPassForm(Form):
    password = PasswordField( _('Password'), [
            validators.Length(min=6, max=120) ] )
    password_confirm = PasswordField( _('Confirm Password'), [
            my_password_confirm ] )


class ResetPassApplyForm(Form):
    email = TextField( _('Email Address'), [validators.Length(min=6, max=35), validators.Email()])


class BaseInfoForm(Form):
    nickname = TextField( _('Nickname'), [
            validators.Length(min=1, max=64) ] )
    first_name = TextField( _('First Name'), [
            validators.Length(max=32) ] )
    last_name = TextField( _('Last Name'), [
            validators.Length(max=32) ] )
#    gender = BooleanField( _('Gender') )
    language = SelectField( _('Language') )


class AvatarForm(Form):

    avatar = FileField( _('Logo') )


class PublicKeyForm(Form):

    name = TextField( _('Name'), [
            validators.Length(min=1, max=128) ] )
    key = TextAreaField( _('Public Key'), [
            validators.Length(min=1, max=1024) ] )
    isdefault = BooleanField( _("Is Default") , default=False)


class EmailValidateForm(Form):
    email = TextField( _('Email Address'), [
            validators.Length(min=6, max=35), validators.Email()])



class OpenIDNewForm(Form):

    email = TextField( _('Email Address'), [
            validators.Length(min=6, max=35), validators.Email()] )

    username = TextField( _('Username'), [
            validators.Length(min=2, max=21)] )

    password = PasswordField( _('Password'), [
            validators.Length(min=6, max=120) ] )

    password_confirm = PasswordField( _('Confirm Password'), [
            my_password_confirm ] )


    def validate_email(form, field):
        user = form._handler.db.query(User).filter_by(
            email = field.data ).first()

        if user:
            raise ValidationError( _('This email is exist.') )

    def validate_username(form, field):
        user = form._handler.db.query(User).filter_by(
            username = field.data ).first()

        if user:
            raise ValidationError( _('This username is occupied.') )

