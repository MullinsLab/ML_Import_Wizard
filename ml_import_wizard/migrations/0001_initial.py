# Generated by Django 4.1.5 on 2023-04-25 18:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportScheme',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('importer', models.CharField(editable=False, max_length=255)),
                ('importer_hash', models.CharField(editable=False, max_length=32)),
                ('public', models.BooleanField(default=True)),
                ('settings', models.JSONField(default=dict)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeFile',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('settings', models.JSONField(default=dict)),
                ('import_scheme', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='ml_import_wizard.importscheme')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeFileStatus',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('uploaded', models.BooleanField(default=False)),
                ('preinspected', models.BooleanField(default=False)),
                ('inspecting', models.BooleanField(default=False)),
                ('inspected', models.BooleanField(default=False)),
                ('importing', models.BooleanField(default=False)),
                ('imported', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeStatus',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('files_received', models.BooleanField(default=False)),
                ('files_inspected', models.BooleanField(default=False)),
                ('data_previewed', models.BooleanField(default=False)),
                ('import_defined', models.BooleanField(default=False)),
                ('import_started', models.BooleanField(default=False)),
                ('import_completed', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeRowRejected',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('errors', models.JSONField(verbose_name='Why was this row rejected by the importer?')),
                ('row', models.JSONField(verbose_name='Complete data for the row that was rejected')),
                ('import_scheme', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rejected_rows', to='ml_import_wizard.importscheme')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeRowDeferred',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('model', models.TextField(max_length=255)),
                ('pkey_name', models.CharField(default='pk', max_length=255)),
                ('pkey_int', models.IntegerField(null=True)),
                ('pkey_str', models.TextField(null=True)),
                ('import_scheme', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deferred_rows', to='ml_import_wizard.importscheme')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportSchemeFileField',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('sample', models.TextField(blank=True, null=True)),
                ('import_scheme_file', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='ml_import_wizard.importschemefile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='importschemefile',
            name='status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='files', to='ml_import_wizard.importschemefilestatus'),
        ),
        migrations.AddField(
            model_name='importscheme',
            name='status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='schemes', to='ml_import_wizard.importschemestatus'),
        ),
        migrations.AddField(
            model_name='importscheme',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ImportSchemeItem',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('app', models.CharField(max_length=255, verbose_name='App this import item is for')),
                ('model', models.CharField(max_length=255, verbose_name='Model this import item is for')),
                ('field', models.CharField(max_length=255, verbose_name='DB Field this import item is for')),
                ('strategy', models.CharField(max_length=255, null=True, verbose_name='Strategy for doing this import')),
                ('settings', models.JSONField(default=dict, verbose_name='Settings specific to this import')),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('import_scheme', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='items', to='ml_import_wizard.importscheme')),
            ],
            options={
                'unique_together': {('import_scheme', 'app', 'model', 'field')},
            },
        ),
    ]
