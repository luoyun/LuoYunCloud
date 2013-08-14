from yweb.forms import Form
from wtforms import validators, DateTimeField, IntegerField, \
     SelectField


class ResourceForm(Form):

    type = SelectField( _('Resource Type') )

    size = IntegerField( _('Resource Size'), [
            validators.NumberRange(min=1) ] )
    
    effect_date = DateTimeField( _('Effect Date') )
    expired_date = DateTimeField( _('Expired Date') )




