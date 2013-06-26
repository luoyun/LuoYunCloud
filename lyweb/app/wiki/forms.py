from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.ext.sqlalchemy.fields import QuerySelectField

from wtforms.validators import ValidationError


from app.wiki.models import WikiCatalog
from yweb.orm import db

def wiki_catalogs():
    return db.query(WikiCatalog).all()

class NewTopicForm(Form):

    name = TextField( _('Name'), [validators.Length(min=2, max=120) ] )
    body = TextAreaField( _('Body'), [validators.Length(min=12, max=10240) ] )
    catalog = QuerySelectField( _('Catalog'), query_factory=wiki_catalogs, get_label='name' )


class TopicForm(Form):

    name = TextField( _('Name'), [validators.Length(min=2, max=120) ] )
    body = TextAreaField( _('Body'), [validators.Length(min=12, max=10240) ] )
    catalog = QuerySelectField( _('Catalog'), query_factory=wiki_catalogs, get_label='name' )


