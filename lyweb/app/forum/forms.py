from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, FileField, HiddenField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError


def password_confirm(form, field):
    if field.data != form.password_confirm.data:
        raise ValidationError( _('password confirm failed') )


class ResetPasswordApplyForm(Form):
    email = TextField( _('Email Address'), [
            validators.Length(min=6, max=35), validators.Email() ] )


class TopicForm(Form):

    catalog = SelectField( _('Catalog') )

    name = TextField( _('Name'), [
            validators.Length(min=2, max=128) ] )

    summary = TextAreaField( _('Summary'), [
            validators.Length(min=2, max=1024) ] )

    tag = TextField( _('Tag') )

    body = TextAreaField( _('Body'), [
            validators.Length(min=2, max=1024*100) ] )


class PostForm(Form):

    body = TextAreaField( _('Body'), [
            validators.Length(min=2, max=1024*100) ] )



from .models import ForumCatalog
class CatalogForm(Form):

    name = TextField( _('Name'), [
            validators.Length(min=2, max=128) ] )

    summary = TextAreaField( _('Summary'), [
            validators.Length(min=2, max=1024) ] )

    description = TextAreaField( _('Description'), [
            validators.Length(max=1024*20) ] )

    def validate_name(form, field):
        old = form._handler.db.query(ForumCatalog).filter_by(
            name = field.data).first()
        if old:
            raise ValidationError( _('This name is exist.') )
