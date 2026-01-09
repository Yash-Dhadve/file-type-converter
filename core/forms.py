from django import forms

class MultiFileInput(forms.FileInput):
    allow_multiple_selected = True

class BatchPDFUploadForm(forms.Form):
    files = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True, 'accept': '.pdf'}),
        required=False
    )
