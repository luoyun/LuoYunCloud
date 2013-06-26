from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, FileField

from wtforms.validators import ValidationError


class NodeEditForm(Form):
    vmemory = IntegerField( _('Virtual Memory(G)'), [validators.NumberRange(min=1, max=1024)])
    vcpus = IntegerField( _('Virtual CPUs'), [validators.NumberRange(min=1, max=1024)])

