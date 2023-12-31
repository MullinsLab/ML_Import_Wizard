# Generated by Django 4.1.5 on 2023-04-04 14:58

from django.db import migrations


def load_initial_data(apps, schema_editor):
    """ Import initial data for ImportSchemeStatus and ImportSchemeFileStatus """

    ImportSchemeStatus = apps.get_model("ml_import_wizard", "ImportSchemeStatus")
    ImportSchemeFileStatus = apps.get_model("ml_import_wizard", "ImportSchemeFileStatus")

    scheme_statuses: list = [
        {"name": "New", "files_received": False, "files_inspected": False, "import_defined": False, "data_previewed": False, "import_started": False, "import_completed": False},
        {"name": "Files Received", "files_received": True, "files_inspected": False, "import_defined": False, "data_previewed": False, "import_started": False, "import_completed": False},
        {"name": "Files Inspected", "files_received": True, "files_inspected": True, "import_defined": True,"data_previewed": False, "import_started": False, "import_completed": False},
        {"name": "Import Defined", "files_received": True, "files_inspected": True, "import_defined": True,"data_previewed": False, "import_started": False, "import_completed": False},
        {"name": "Data Previewed", "files_received": True, "files_inspected": True, "import_defined": True,"data_previewed": True, "import_started": False, "import_completed": False},
        {"name": "Import Started", "files_received": True, "files_inspected": True, "import_defined": True,"data_previewed": True, "import_started": True, "import_completed": False},
        {"name": "Import Completed", "files_received": True, "files_inspected": True, "import_defined": True,"data_previewed": True, "import_started": True, "import_completed": True},

    ]
    file_statuses: list = [
        {"name": "New", "uploaded": False, "preinspected": False, "inspecting": False, "inspected": False, "importing": False, "imported": False},
        {"name": "Uploaded", "uploaded": True, "preinspected": False, "inspecting": False, "inspected": False, "importing": False, "imported": False},
        {"name": "Preinspected", "uploaded": True, "preinspected": True, "inspecting": False, "inspected": False, "importing": False, "imported": False},
        {"name": "Inspecting", "uploaded": True, "preinspected": True, "inspecting": True, "inspected": False, "importing": False, "imported": False},
        {"name": "Inspected", "uploaded": True, "preinspected": True, "inspecting": True, "inspected": True, "importing": False, "imported": False},
        {"name": "Importing", "uploaded": True, "preinspected": True, "inspecting": True, "inspected": True, "importing": True, "imported": False},
        {"name": "Imported", "uploaded": True, "preinspected": True, "inspecting": True, "inspected": True, "importing": True, "imported": True},
    ]

    for scheme_status in scheme_statuses:
        status = ImportSchemeStatus(**scheme_status)
        status.save()

    for file_status in file_statuses:
        status = ImportSchemeFileStatus(**file_status)
        status.save()


def reverse_func(apps, schema_editor):
    """ Remove out statuses if a reverse is done """

    ImportSchemeStatus = apps.get_model("ml_import_wizard", "ImportSchemeStatus")
    ImportSchemeFileStatus = apps.get_model("ml_import_wizard", "ImportSchemeFileStatus")

    ImportSchemeStatus.objects.all().delete()
    ImportSchemeFileStatus.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ml_import_wizard', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data, reverse_func)
    ]
