from django import forms

class MultiFileInput(forms.FileInput):
    allow_multiple_selected = True

class SinglePDFUploadForm(forms.Form):
    file = forms.FileField(label="Upload PDF")

class BatchPDFUploadForm(forms.Form):
    files = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=False,   # 🔥 IMPORTANT
        label="Upload PDFs"
    )

