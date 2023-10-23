from django.conf import settings
from django.apps import AppConfig

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard.utils.importer import setup_importers


class ImportWizardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_import_wizard'
    verbose_name = 'Mullins Lab Import Wizard'

    def ready(self) -> None:
        """ Initialize the importer objects from settings """

        if settings.ML_IMPORT_WIZARD.get("Setup_On_Start", True):
            setup_importers()
        