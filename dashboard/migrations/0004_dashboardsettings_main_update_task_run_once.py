# Generated by Django 4.0.10 on 2023-02-28 00:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_dashboardsettings_delay_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboardsettings',
            name='main_update_task_run_once',
            field=models.BooleanField(default=False),
        ),
    ]
