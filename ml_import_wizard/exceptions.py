from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

import inspect

class LoggingException(Exception):
    """ Class to inherit if we want exceptions logged """
    def __init__(self, message: str=''):
        message = f"{inspect.stack()[1].filename}:{inspect.stack()[1].lineno} ({inspect.stack()[1].function}) {message}"

        if settings.ML_IMPORT_WIZARD['Log_Exceptions']:
            log.warn(message)
            
        self.message = message

    def __str__(self) -> str:
        return self.message


class MLImportWizardNotReady(LoggingException):
    """ ML Import Wizard is not ready.  Invalid ML_IMPORT_WIZARD setting, or ml_import_wizard.utils.importer.import.inspect_models not run. """


class GFFUtilsNotInstalledError(LoggingException):
    """ GFF & GFF3 Files can't be inspected because gffutils is not installed """


class FileNotReadyError(LoggingException):
    """ File can't be operated on because it isn't ready """


class UnresolvedInspectionOrder(LoggingException):
    """ Inspection can't resolve the order of models for importing """


class ImportSchemeNotReady(LoggingException):
    """ The import scheme isn't ready for some reason """


class StatusNotFound(LoggingException):
    """ The indicated status has not been found """