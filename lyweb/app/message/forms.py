from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.ext.sqlalchemy.fields import QuerySelectField

from wtforms.validators import ValidationError


from yweb.orm import db


class NewMessageForm(Form):

    sendto = TextField( _('Send To') )
    subject = TextField( _('Subject'), [validators.Length(min=2, max=120) ] )
    content = TextAreaField( _('Content'), [validators.Length(min=6, max=10240) ] )

class ReplyMessageForm(Form):
    
    subject = TextField( _('Subject'), [validators.Length(min=2, max=120) ] )
    content = TextAreaField( _('Content'), [validators.Length(min=6, max=20480) ] )


class MessageForm(Form):

    to = TextField( _('To') )
    subject = TextField( _('Subject'), [validators.Length(min=2, max=256) ] )
    text = TextAreaField( _('Text'), [validators.Length(min=6, max=10240) ] )
