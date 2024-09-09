""" Holds functions that deal with file processing """

from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard import models


def check_processes() -> None:
    """ Checks running processes for crashes """

    # Update status if scheme has all files inspected
    for scheme in models.ImportScheme.objects.filter(status__files_received=True, status__files_inspected=False):
        if scheme.all_files_inspected:
            scheme.set_status_by_name("Files Inspected")
            scheme.save()

            log.warn(f"{scheme} has all files inspected, setting status to 'Files Inspected'")


    # Check for crashed imports
    for scheme in models.ImportScheme.objects.filter(status__import_started=True, status__import_completed=False, status__import_failed=False):
        scheme.process_check_health()
        

def start_next_process() -> None:
    """ Starts the next process in the queue """

    # Run a file inspection
    if scheme_file := models.ImportSchemeFile.objects.filter(status__preinspected=True, status__inspecting=False).first():
        log.warn(f"Starting process {scheme_file}")
        scheme_file.inspect()

        return scheme_file

    # Check to see how many processes are running
    count: int = models.ImportScheme.objects.filter(status__import_started=True, status__import_completed=False, status__import_failed=False).count()

    if count >= settings.ML_IMPORT_WIZARD['Max_Importer_Processes']:
        log.warn(f"Max importer processes reached ({count})")
        return False
    
    # Run an import
    if scheme := models.ImportScheme.objects.filter(status__data_previewed=True, status__import_started=False).first():
        log.warn(f"Starting process {scheme}")  
        scheme.process_run()

        return scheme
    
    return False