# Generated by Django 4.0.10 on 2023-03-01 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0003_rename_item_id_release_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='last_viewed_as_preorder',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]