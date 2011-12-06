from django import forms

from lyweb.app.domain.models import Domain
from lyweb import LuoYunConf as lyc


class DomainSimpleCreateForm(forms.ModelForm):

    class Meta:
        model = Domain
        fields = ['name', 'diskimg']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(DomainSimpleCreateForm, self).__init__(*args, **kwargs)

    def save(self, commit = True):
        domain = super(DomainSimpleCreateForm, self).save(commit = False)
        domain.diskimg = self.cleaned_data['diskimg']
        name = self.cleaned_data['name']
        domain.name = name if name else "lmi-%s" % domain.diskimg
        domain.user = self.user
        domain.save() # get the id !
        # TODO: id >= 65536
        domain.mac = '92:1B:40:26:%02x:%02x' % (
            domain.id / 256, domain.id % 256)
        domain.save()
        return domain
