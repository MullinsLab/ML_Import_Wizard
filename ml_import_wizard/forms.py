from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset

from .models import ImportScheme


class NewImportSchemeForm(forms.ModelForm):
    ''' Start a new import scheme '''
    class Meta:
        model = ImportScheme
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        ''' Specify information about the display of the form '''
        importer = kwargs.pop('importer_slug', None)

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'new_import_scheme'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Fieldset(
                'New {{importer}} Import',
                'name',
                'description',
            )
        )

        self.helper.add_input(Submit('submit', 'Submit'))


class UploadFileForImportForm(forms.Form):
    ''' Get a file to start importing from '''
    file1 = forms.FileField()
    file2 = forms.FileField(required=False)
    file3 = forms.FileField(required=False)
    file4 = forms.FileField(required=False)
    file5 = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        ''' Specify information about the display of the form '''
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'upload_form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'

        self.helper.add_input(Submit('submit', 'Submit'))