from yweb.forms import Form
from wtforms import BooleanField, TextField, validators



class DomainForm(Form):

    # TODO: make sure it's a valid domain
    topdomain = TextField( _('Top domain'), [ validators.Length(min=6, max=120) ] )
    prefix = TextField( _('Name prefix') )
    suffix = TextField( _('Name suffix') )


