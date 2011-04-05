
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

    ignored = 0
    
    for api in meta.getAPIMethods():
      if api.startswith("set") and (not main_meta or (main_meta and self.data[api] != '')):
        widget = forms.Textarea if api in ['setSynopsis',
                                           'setTitleEpisodeTitle',
                                           'setTitleSeriesTitle'] \
                 else forms.TextInput
                 
        self.fields[api] = forms.CharField(required=False,
                                           widget=widget,
                                           label=metadata.HUMAN_DESCRIPTION.get(
                                             meta.method2attrib[api]))
      else:
        ignored += 1
    self.fields['filename'] = forms.CharField(required=False, widget=forms.HiddenInput)
    self.fields['should_cascade'] = forms.ChoiceField(required=False, 
                                                      widget=forms.HiddenInput, 
                                                      choices=[('False', 'False'), 
                                                               ('True', 'True')])

    #print len(self.fields), len(meta.getAPIMethods()), ignored, main_meta, self.data.values()

class AddFeedForm(forms.Form):
  url = forms.CharField(required=True)
  
class PathForm(forms.Form):
  path = forms.CharField(max_length=300, required=True)
  
  def clean_path(self):
    if not self.cleaned_data['path'].startswith(settings.FEED_DIR):
      return settings.FEED_DIR+self.cleaned_data['path']
    else:
      return self.cleaned_data['path']
    
class CreateFeedForm(forms.Form):
  title = forms.CharField(required=True, max_length=200)
  description = forms.CharField(required=True, max_length=600)
  originator = forms.CharField(required=True, max_length=200)
  publisher = forms.CharField(required=True, max_length=200)
  language = forms.CharField(required=True, max_length=2)
    

class ListDirForm(forms.Form):
    dir = forms.CharField(max_length=300, required=False)

    def clean_dir(self):
        dir = self.cleaned_data['dir']
        if dir[-1:] != '/':
            dir += '/'
        return dir

class AddItemForm(forms.Form):
  feed_dir = forms.CharField(required=False, widget=forms.HiddenInput)
  file = forms.CharField(required=True, max_length=200)
  synopsis = forms.CharField(required=True, max_length=600)
  title = forms.CharField(required=True, max_length=100)
