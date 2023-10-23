from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard.models import ImportSchemeFile
from ml_import_wizard.exceptions import GFFUtilsNotInstalledError, FileNotReadyError
# from ml_import_wizard.utils.import_files import GFFImporter

class Command(BaseCommand):
    help = "Inspects a file in preperation for importing. This is not intended to be run by humans, it's there for the system to run outside of page views. "
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def add_arguments(self, parser):
        ''' Set the arguments for InspectFile '''
        parser.add_argument('import_file_id', nargs='+', type=int, help='The ID(s) of the ImportFile(s) to inspect')

        parser.add_argument(
            '--use_db',
            action='store_true',
            help="Use the existing DB instead of building a new one (only for GFF and GFF3 files).",
        )

        parser.add_argument(
            '--ignore_status',
            action='store_true',
            help="Inspect the file even if it has already been inspected.",
        )

    def handle(self, *args, **options):
        ''' Do the work of inspecting a file '''
        
        files_count: int = 0
        verbosity: int = int(options['verbosity'])

        for import_file_id in options['import_file_id']:
            try:
                import_scheme_file = ImportSchemeFile.objects.get(pk=import_file_id)
            except ImportSchemeFile.DoesNotExist as err:
                log.warn(f'ImportFile {import_file_id} does not exist')
                raise CommandError(f'ImportFile {import_file_id} does not exist')
                
            if verbosity > 1:
                self.stdout.write(f'Starting to inspect {import_scheme_file} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{import_scheme_file.file_name}) file.')

            try:
                import_scheme_file.inspect(use_db=options['use_db'], ignore_status=options['ignore_status'])
            except (FileNotReadyError, GFFUtilsNotInstalledError) as err:
                raise CommandError(err)
            
            if verbosity > 1:
                self.stdout.write(f'You done inspected that {import_scheme_file} ({settings.ML_IMPORT_WIZARD["Working_Files_Dir"]}{import_scheme_file.file_name}) file!')

            files_count += 1

        if not files_count: self.stdout.write(self.style.FAILURE(f'No files inspected.'))
        elif files_count == 1: self.stdout.write(self.style.SUCCESS(f'1 file inspected.'))
        else: self.stdout.write(self.style.SUCCESS(f'{files_count} files inspected.'))
