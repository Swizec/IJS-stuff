
from django import forms
from django.conf import settings

from JSI.RichMetadata.RichMetadata import RichMetadataGenerator
from JSI.RichMetadata.conf import metadata

class MetaForm(forms.Form):
  def __init__(self, *args, **kwargs):
    try:
      main_meta = kwargs.pop('main_meta')
    except KeyError:
      main_meta = False
      
    super(MetaForm, self).__init__(*args, **kwargs)
    
    rmg = RichMetadataGenerator.getInstance()
    meta = rmg.getRichMetadata()
    
    for api in meta.getAPIMethods():
      if api.startswith("set") and (not main_meta or (main_meta and self.data[api] != '')):
        self.fields[api] = forms.CharField(required=False,
                                           label=metadata.HUMAN_DESCRIPTION.get(meta.method2attrib[api]))
    self.fields['filename'] = forms.CharField(required=False, widget=forms.HiddenInput)
    self.fields['should_cascade'] = forms.ChoiceField(required=False, 
                                                      widget=forms.HiddenInput, 
                                                      choices=[('False', 'False'), 
                                                               ('True', 'True')])

class AddFeedForm(forms.Form):
  url = forms.CharField(required=True)
    

class ListDirForm(forms.Form):
    dir = forms.CharField(max_length=300, required=False)

    def clean_dir(self):
        dir = self.cleaned_data['dir']
        if dir[-1:] != '/':
            dir += '/'
        return dir
