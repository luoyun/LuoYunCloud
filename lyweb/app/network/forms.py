from yweb.forms import Form
from wtforms import BooleanField, TextField, \
    validators, DateTimeField, TextAreaField, IntegerField, \
    PasswordField, SelectMultipleField, FileField, SelectField

from wtforms.ext.sqlalchemy.fields import QuerySelectField

from wtforms.validators import ValidationError, NumberRange

import settings

import IPy


def ipcheck(form, field):
    try:
        IPy.parseAddress(field.data)
    except ValueError, msg:
        # msg is "single byte must be 0 <= byte < 256"
        raise ValidationError(msg)


def multi_ipcheck(form, field):
    error = []
    for x in field.data.split():
        try:
            IPy.parseAddress(x)
        except ValueError:
            error.append( x )

    if error:
        raise ValidationError( _('Error IP: %s') % error )


class NetworkPoolForm(Form):

    name = TextField( _('Name'), [ validators.Length(min=2, max=128) ] )
    description = TextAreaField( _('Description') )

    start = TextField( _('Start IP'), [ ipcheck ] )
    end = TextField( _('End IP'), [ ipcheck ] )
    netmask = TextField( _('Netmask'), [ ipcheck ] )
    gateway = TextField( _('Gateway'), [ ipcheck ] )
    nameservers = TextAreaField( _('Nameservers'), [ multi_ipcheck, validators.Length(max=1024) ] )
    exclude_ips = TextAreaField( _('Exclude ip list'), [ multi_ipcheck ] )



from .models import Gateway

class GatewayForm(Form):

    name = TextField( _('Name'), [ validators.Length(min=2, max=64) ] )
    description = TextAreaField( _('Description') )

    ip      = TextField( _('IP'), [ipcheck] )
    netmask = TextField( _('Netmask'), [ ipcheck ] )

    start = IntegerField( _('Start Port'), [
            NumberRange( min = 9999, max = 65535 ) ] )
    end   = IntegerField( _('End Port'), [
            NumberRange( min = 9999, max = 65535 ) ] )

    exclude_ports = TextAreaField( _('Exclude Ports') )


    def validate_ip(form, field):
        if not form._handler.gateway:
            old = form._handler.db.query(Gateway).filter_by(
                ip = field.data).first()

            if old:
                raise ValidationError( _('This ip exists.') )

    def validate_exclude_ports(form, field):
        error = []
        for x in field.data.split():
            try:
                int( x.strip() )
            except ValueError:
                error.append( x )

        if error:
            raise ValidationError( _('Error Ports: %s') % error )



