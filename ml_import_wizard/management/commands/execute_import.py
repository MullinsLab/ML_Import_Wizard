from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard.models import ImportScheme
from ml_import_wizard.exceptions import ImportSchemeNotReady, GFFUtilsNotInstalledError

class Command(BaseCommand):
    help = " Imports all data for an importer into the database.  This is not intended to be run by humans, it's there for the system to run outside of page views. "
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def add_arguments(self, parser):
        ''' Set the arguments for execute_import '''
        parser.add_argument('import_scheme_id', nargs='+', type=int, help='The ID(s) of the ImportFile(s) to inspect')
        parser.add_argument('--limit_count', nargs='?', default=None, type=int, help='Number of rows to import from the file.')
        parser.add_argument('--offset_count', nargs='?', default=None, type=int, help='Number of rows to skip at the beginning of the file.')
        parser.add_argument('--ignore_status', action='store_true', help="Inspect the file even if it has already been inspected.")

    def handle(self, *args, **options):
        ''' Do the work of inspecting a file '''
        
        verbosity: int = int(options['verbosity'])

        for import_scheme_id in options['import_scheme_id']:
            try:
                import_scheme = ImportScheme.objects.get(pk=import_scheme_id)
            except ImportScheme.DoesNotExist as err:
                log.warn(f'ImportScheme {import_scheme_id} does not exist')
                raise CommandError(f'ImportScheme {import_scheme_id} does not exist')
            
            if verbosity > 1:
                self.stdout.write(f'Starting to import {import_scheme} (import_scheme.importer)')

            # try:
            #     import_scheme.execute(ignore_status=options['ignore_status'], limit_count=options['limit_count'], offset_count=options["offset_count"])
            # except Exception as err:
            #     raise CommandError(err)
            
            import_scheme.execute(ignore_status=options['ignore_status'], limit_count=options['limit_count'], offset_count=options["offset_count"])

            # print(f"Limit Count: {options['limit_count']}")

            self.stdout.write(self.style.SUCCESS(f'{import_scheme} ({import_scheme.id}) has been imported.'))
            
