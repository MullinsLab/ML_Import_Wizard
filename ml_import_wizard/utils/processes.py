""" Holds functions that deal with file processing """

from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard import models


def check_processes() -> None:
    """ Checks running processes for crashes """

    for scheme in models.ImportScheme.objects.filter(status__import_started=True, status__import_finished=False, status__import_failed=False):
        scheme.check_process_health()
        

def start_next_process() -> None:
    """ Starts the next process in the queue """
    
    schemes = models.ImportScheme.objects.filter(status__data_previewed=True, status__import_started=False)

    if models.ImportScheme.objects.filter(status__data_previewed=True, status__import_started=False).count() < settings.ML_IMPORT_WIZARD.get("Max_Importer_Processes", 1):
        if scheme := models.ImportScheme.objects.filter(status__data_previewed=True, status__import_started=False).first():
            log.warn(f"Starting process {scheme}")  
            #scheme.process_run()

            return scheme
    
    return False