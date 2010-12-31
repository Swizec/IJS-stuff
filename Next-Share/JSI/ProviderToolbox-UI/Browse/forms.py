
from django import forms
from django.conf import settings

class AddForm(forms.Form):
    title = forms.CharField(max_length=200, required=True)
    genre = forms.ChoiceField(choices=[], required=False)
    minimum_age = forms.IntegerField(required=False)
    language = forms.CharField(max_length=2, required=False)
    caption_language = forms.CharField(max_length=2, required=False)
    sign_language = forms.CharField(max_length=2, required=False)
    is_interactive_content = forms.BooleanField(required=False, widget=forms.NullBooleanSelect)
    is_commercial_content = forms.BooleanField(required=False, widget=forms.NullBooleanSelect)
    contains_commercial_content = forms.BooleanField(required=False, widget=forms.NullBooleanSelect)
    bitrate = forms.ChoiceField(required=False, choices=[('44kbps', '44kbps'),
                                                        ('128kbps', '128kbps'),])
    description = forms.CharField(max_length=700, widget=forms.Textarea, required=False)

class ListDirForm(forms.Form):
    dir = forms.CharField(max_length=300, required=False)

    def clean_dir(self):
        dir = self.cleaned_data['dir']
        if dir[-1:] != '/':
            dir += '/'
        return dir
