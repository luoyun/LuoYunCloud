from django import forms

from lyweb.app.image.models import Image
from lyweb import LuoYunConf as lyc

import os


def list_file(path):

    L = []
    a = os.listdir(path)
    for f in a:
        ff = os.path.join(path, f)
        if os.path.isfile(ff):
            L.append( (f, f) )

    return tuple(L)


class ImageRegisterForm(forms.ModelForm):

    #path = forms.CharField(max_length = 128,
    #         widget = forms.Select(choices = list_file(lyc.LY_IMAGE_UPLOAD_PATH)))
    path = forms.CharField(max_length = 128)

    class Meta:
        model = Image
        fields = ['name', 'type']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ImageRegisterForm, self).__init__(*args, **kwargs)

    def save(self, commit = True):
        image = super(ImageRegisterForm, self).save(commit = False)
        image.user = self.user
        name = self.cleaned_data['name']
        path = self.cleaned_data['path']
        image.name = name if name else path
        image.type = self.cleaned_data['type']
        image.checksum(path)

        try:
            I = Image.objects.get(checksum_value = image.checksum_value)
            if I:
                return None # Image exists
        except:
            pass

        src_path = os.path.join( lyc.LY_IMAGE_UPLOAD_PATH, path )
        image.size = os.path.getsize( src_path )
        image.save() # TODO: get the image id

        dst_path = os.path.join( lyc.LY_IMAGE_PATH, image.path )
        try:

            if not os.path.exists( dst_path ):
                os.link( src_path, dst_path )
            os.unlink( src_path )
        except KeyError:
            pass # Fix me

        return image
