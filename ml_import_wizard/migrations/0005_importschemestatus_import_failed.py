# Generated by Django 4.1.5 on 2024-08-14 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ml_import_wizard", "0004_importscheme_process_created_time_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="importschemestatus",
            name="import_failed",
            field=models.BooleanField(default=False),
        ),
    ]
