from django import forms

from lyweb.app.node.models import Node
from lyweb import LuoYunConf as lyc


class NodeRegisterForm(forms.ModelForm):

    class Meta:
        model = Node
        fields = ['hostname', 'ip', 'port']

    def __init__(self, *args, **kwargs):
        super(NodeRegisterForm, self).__init__(*args, **kwargs)

    def save(self, commit = True):
        node = super(NodeRegisterForm, self).save(commit = False)
        self.hostname = self.cleaned_data['hostname']
        self.ip = self.cleaned_data['ip']
        self.port = int(self.cleaned_data['port'])
        node.save()
        return node
