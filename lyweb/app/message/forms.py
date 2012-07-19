from lyforms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.ext.sqlalchemy.fields import QuerySelectField

from wtforms.validators import ValidationError


from app.wiki.models import WikiCatalog
from lyorm import db


class NewMessageForm(Form):

    sendto = TextField( _('Send To') )
    subject = TextField( _('Subject'), [validators.Length(min=6, max=200) ] )
    content = TextAreaField( _('Content'), [validators.Length(min=12, max=10240) ] )

class ReplyMessageForm(Form):
    
    subject = TextField( _('Subject'), [validators.Length(min=6, max=200) ] )
    content = TextAreaField( _('Content'), [validators.Length(min=12, max=20480) ] )

