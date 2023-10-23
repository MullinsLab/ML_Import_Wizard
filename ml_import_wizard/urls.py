from django.contrib.auth.decorators import login_required
from django.urls import path, include

from ml_import_wizard.views import *

app_name='ml_import_wizard'

urlpatterns = [
    path('', ManageImports.as_view(), name='import'),
    path('<int:import_scheme_id>', DoImportScheme.as_view(), name='scheme'),
    path('<int:import_scheme_id>/list', ListImportSchemeItems.as_view(), name='scheme_list_items'),
    path('<int:import_scheme_id>/preview', PreviewImportScheme.as_view(), name='scheme_preview_items'),
    path('<int:import_scheme_id>/description', DescribeImportScheme.as_view(), name='scheme_description'),
    path('<int:import_scheme_id>/<int:import_item_id>', DoImportSchemeItem.as_view(), name='scheme_item'),
    path('<int:import_scheme_id>/<str:model_name>', DoImporterModel.as_view(), name='importer_model'),
    path('<slug:importer_slug>', NewImportScheme.as_view(), name='new_scheme'),
]