from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, FileField, HiddenField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import ValidationError

from .models import entry_type
_entry_type = [(str(x), y) for x, y in entry_type]


class SiteNavForm(Form):

    language = SelectField( _('Language') )

    name = TextField( _('Name'), [
            validators.Length(min=2, max=64) ] )

    type = SelectField( _('Type'), choices=_entry_type )

    target  = TextField( _('Target'), [
            validators.Length(min=1, max=64) ] )

    summary = TextAreaField( _('Summary'), [
            validators.Length(min=2, max=256) ] )

    isnewopen = BooleanField( _('Open with new windows') )


class SiteEntryForm(Form):

    slug  = TextField( _('Slug'), [
            validators.Length(min=1, max=64) ] )


class ArticleForm(Form):

    entry    = SelectField( _('Site Entry') )
    language = SelectField( _('Language') )

    name = TextField(_('Name'), [validators.Length(min=2, max=64)])
    summary = TextAreaField(_('Summary'), [validators.Length(max=256) ])
    body = TextAreaField(_('Body'), [validators.Length(max=10240)])
    is_visible = BooleanField( _('Is it visible ?'))

class ArticleEditForm(Form):

    name = TextField(_('Name'), [validators.Length(min=2, max=64)])
    summary = TextAreaField(_('Summary'), [validators.Length(max=256) ])
    body = TextAreaField(_('Body'), [validators.Length(max=10240)])
    is_visible = BooleanField( _('Is it visible ?'))


class SiteConfigForm(Form):

    key = TextField(_('Key'), [validators.Length(min=2, max=256)])
    value = TextAreaField(_('value'), [validators.Length(max=1024)])


class SiteLocaleConfigForm(Form):

    language = SelectField( _('Language') )
    key = TextField(_('Key'), [validators.Length(min=2, max=256)])
    value = TextAreaField(_('value'), [validators.Length(max=1024)])

