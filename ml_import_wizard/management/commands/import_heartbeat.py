from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard.utils.processes import start_next_process
from ml_import_wizard.exceptions import ImportSchemeNotReady, GFFUtilsNotInstalledError


class Command(BaseCommand):
    help = " Checks for import jobs that are ready to run.  This is not intended to be run by humans, it's there for the system to run outside of page views. "
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def add_arguments(self, parser):
        """ Set the arguments for execute_import, currently there aren't any """
        
        pass
        
    def handle(self, *args, **options):
        ''' Do the work of inspecting a file '''
        if scheme := start_next_process():
            self.stdout.write(self.style.SUCCESS(f'{scheme} ({scheme.id}) has been processed.'))
        
        else:
            self.stdout.write(self.style.SUCCESS(f'No import jobs ready to run.'))