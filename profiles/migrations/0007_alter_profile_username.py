# Generated by Django 4.0.10 on 2023-03-01 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_remove_profile_img_url_profile_img_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='username',
            field=models.TextField(blank=True, null=True, unique=True),
        ),
    ]