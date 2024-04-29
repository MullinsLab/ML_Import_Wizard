ML Import Wizard is a user facing Django app that takes flat square data files, or linked flat square data files, and decomposes them for importing into a Django ORM.  One of the weaknesses of an ORM is that while it does a good job turning data tables into objects, they are not great at composing objects into larger structures.  Toward this end ML Import Wizard uses introspection to observe Django models and their relationships, and uses that information to create needed Django objects from the import.

It is designed to take input data files as they are, associating fields with Django model attributes, including the ability to combine, split, and transform data in fields to fit them into the ORM.  It will allow importing into many (dozens or hundreds of) models at a time.  It will import data coherently across multiple apps.

As a user facing tool, it is designed to allow end users to manage their own data imports without having to go to the database back end or use the Admin tools.


Sample settings structure:
```python
ML_IMPORT_WIZARD = {
    "Working_Files_Dir": os.path.join("/", env("WORKING_FILES_DIR"), ""),
    "Logger": "app",
    "Log_Exceptions": True,
    "Setup_On_Start": True,
    'Importers': {
        'Genome': {
            'name': 'Genome',
            'description': 'Import an entire genome',
            'apps': [
                {
                    'name': 'core',
                    'include_models': ['GenomeSpecies', "GenomeVersion", "GeneType", "FeatureType", "Feature", "FeatureLocation"],
                    # 'exclude_models': ['Feature'],
                    'models': {
                        'GenomeSpecies': {
                            'restriction': 'deferred',
                            "load_value_fields": ["genome_species_name"],
                        },
                        "GenomeVersion": {
                            "exclude_fields": ['external_gene_id_source'],
                            "default_option": "raw_text",
                            "load_value_fields": ["genome_version_name"],
                        },
                        'FeatureType': {
                            'restriction': 'rejected',
                            'fields': {
                                'feature_type_name': {
                                    'approved_values': ['CDS', 'exon', 'region', 'gene', 'start_codon', 'stop_codon']
                                },
                            },
                        },
                        "Feature": {
                            # "exclude_fields": ["external_gene_id"],
                        },
                        'FeatureLocation': {
                            "fields": {
                                "feature_orientation": {
                                    "critical": True,
                                    "translate_values": {"+": "F", "-": "R"},
                                    "force_case": "upper",  
                                },
                            },
                        },
                    },
                },
            ],
        },
    }
}
```
