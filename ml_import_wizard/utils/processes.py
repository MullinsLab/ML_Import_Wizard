""" Holds functions that deal with file processing """

from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard import models


def check_processes() -> None:
    """ Checks running processes for crashes """

    for scheme in models.ImportScheme.objects.filter(status__import_started=True, status__import_completed=False, status__import_failed=False):
        scheme.check_process_health()
        

def start_next_process() -> None:
    """ Starts the next process in the queue """
    
    # Check to see how many processes are running
    count: int = models.ImportScheme.objects.filter(status__import_started=True, status__import_completed=False).count()
    count += models.ImportSchemeFile.objects.filter(status__inspecting=True, status__inspected=False).count()

    if count >= settings.ML_IMPORT_WIZARD['Max_Importer_Processes']:
        log.warn(f"Max importer processes reached ({count})")
        return False

    # Run a file inspection
    if scheme_file := models.ImportSchemeFile.objects.filter(status__preinspected=True, status__inspecting=False).first():
        log.warn(f"Starting process {scheme_file}")
        scheme_file.inspect()

        return scheme_file

    # Run an import
    if scheme := models.ImportScheme.objects.filter(status__data_previewed=True, status__import_started=False).first():
        log.warn(f"Starting process {scheme}")  
        #scheme.process_run()

        return scheme
    
    return False