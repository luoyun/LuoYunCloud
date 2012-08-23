from lyforms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.ext.sqlalchemy.fields import QuerySelectField

from wtforms.validators import ValidationError, NumberRange

import settings


class BaseForm(Form):

    dbhost = TextField( _('server') )
    dbtype = TextField( _('engine') )
    dbuser = TextField( _('username') )
    dbpass = PasswordField( _('password') )
    dbname = TextField( _('db name') )

