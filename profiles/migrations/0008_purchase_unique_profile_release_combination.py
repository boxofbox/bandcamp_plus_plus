# Generated by Django 4.0.10 on 2023-03-06 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0007_alter_profile_username'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='purchase',
            constraint=models.UniqueConstraint(fields=('profile', 'release'), name='unique_profile_release_combination'),
        ),
    ]