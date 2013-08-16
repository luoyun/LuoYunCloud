from yweb.forms import Form
from wtforms import validators, TextField, TextAreaField, \
    SelectField, IntegerField, PasswordField, BooleanField

from wtforms.validators import NumberRange, ValidationError, \
    Required, EqualTo, Regexp

import settings


class PublicKeyForm(Form):

    key = TextAreaField( _('SSH Public Key') )


class BaseinfoForm(Form):

    name = TextField( _('Name'), [
            validators.Length(min=2, max=120) ] )

    summary = TextField( _('Summary') )

    description = TextAreaField( _('Description') )


from app.storage.models import StoragePool
class StorageForm(Form):

    _pool = None

    pool = SelectField( _('Storage Pool') )
    size = IntegerField( _('Size (GB)'), [NumberRange( min = 1 )] )


    def validate_pool(form, field):
        pool = form._handler.db.query(StoragePool).get(field.data)
        if not pool:
            raise ValidationError( _('Invalid pool select.') )

        if form.size.data > pool.remain:
            raise ValidationError( _('Just %sG remain for this pool.') % pool.remain )

        form._pool = pool

    def validate_size(form, field):
        remain = form._handler.current_user.profile.storage_remain
        if remain < field.data:
            raise ValidationError(
                _('You just have %sG storage only.') %  remain )


class ResourceForm(Form):

    cpus = IntegerField( _('CPU'), [
            NumberRange( min = 1 )], default = 1 )

    memory = IntegerField( _('Memory(M)'), [
            NumberRange( min = 64 )], default = 256 )


    def validate_cpus(form, field):
        profile = form._handler.current_user.profile
        if not profile:
            raise ValidationError( _('Error: no user profile.') )

        I = form._handler.I

        if I.is_running:
            available = profile.cpu_remain + I.cpus
        else:
            available = profile.cpu_remain

        if field.data > available:
            raise ValidationError( _('Just %s core available.') % available )


    def validate_memory(form, field):
        profile = form._handler.current_user.profile
        if not profile:
            raise ValidationError( _('Error: no user profile.') )

        I = form._handler.I

        if I.is_running:
            available = profile.memory_remain + I.memory
        else:
            available = profile.memory_remain

        if field.data > available:
            raise ValidationError( _('Just %s M available.') % available )



from app.network.models import NetworkPool
class NetworkForm(Form):

    _pool = None
    _free_ip = None

    pool = SelectField( _('Network Pool') )

    def validate_pool(form, field):
        pool = form._handler.db.query(NetworkPool).get(field.data)
        if not pool:
            raise ValidationError( _('Invalid pool select.') )

        free_ip = pool.get_free_ip()
        if not free_ip:
            raise ValidationError( _('No free ip in this pool.') )

        form._pool = pool
        form._free_ip = free_ip



class PasswordSetForm(Form):

    password = PasswordField( _('New Password'), [ Required(), EqualTo('confirm', message=_('Passwords must match')) ] )
    confirm  = PasswordField( _('Repeat Password') )


class InstancePasswordForm(Form):

    usedefault = BooleanField( _('Use Global Password'), default = True)

    password = PasswordField( _('New Password') )
    confirm  = PasswordField( _('Repeat Password') )

    def validate_password(form, field):

        if not form.usedefault.data:
            if field.data != form.confirm.data:
                raise ValidationError( _('Passwords must match') )



from app.account.models import PublicKey
class InstancePublicKeyForm(Form):

    _key = None

    key = SelectField( _('Key') )

    def validate_key(form, field):
        key = form._handler.db.query(PublicKey).get(field.data)
        if not key:
            raise ValidationError( _('Invalid key select.') )

        form._key = key



class InstanceDomainForm(Form):

    # TODO: simple re
    domain = TextField( _('Domain'), [
            Regexp( r'^(([A-Za-z0-9])+[\.]?)+$',
                    message=_('Invalid domain name.') ) ] )



from app.instance.models import Instance
from sqlalchemy import and_

class InstanceCreateBaseForm(Form):

    name = TextField( _('Name'), [validators.Length(min=2, max=30)] )
    cpus = IntegerField( _('CPU'), [NumberRange( min = 1 )], default = 1 )
    memory = IntegerField( _('Memory(M)'), [NumberRange( min = 64 )], default = 256 )
    isprivate = BooleanField( _('Hide'), default = True )

    def validate_name(form, field):
        I = form._handler.db.query(Instance).filter(
            and_( Instance.name == field.data,
                  Instance.user_id == form._handler.current_user.id
                  ) ).first()
        if I:
            raise ValidationError( _('You have used the name for a instance.') )

    def validate_cpus(form, field):
        profile = form._handler.current_user.profile

        if profile.cpu_remain < field.data:
            raise ValidationError( _('Just have %s core CPU available.') % profile.cpu_remain )

    def validate_memory(form, field):
        profile = form._handler.current_user.profile

        if profile.memory_remain < field.data:
            raise ValidationError( _('Just have %s M memory available.') % profile.memory_remain )


class InstanceCreateForm(InstanceCreateBaseForm):

    appliance = SelectField( _('Appliance') )



from app.network.models import IPPool, PortMapping
class PortMappingForm(Form):

    _ip = None

    ip = SelectField( _('Binding IP') )

    port = IntegerField( _('Locale Port'), [
            NumberRange( min = 20, max = 65535 ) ], default = 22 )

    def validate_ip(form, field):
        ip = form._handler.db.query(IPPool).get(field.data)
        if ( not ip or
             ip.instance_id != form._handler.I.id ):
            raise ValidationError( _('Invalid ip select.') )

        form._ip = ip

    def validate_port(form, field):
        old = form._handler.db.query(PortMapping).filter(
            and_( PortMapping.ip_id == form.ip.data,
                  PortMapping.ip_port == field.data)).first()

        if old:
            raise ValidationError( _('This binding exist.') )


