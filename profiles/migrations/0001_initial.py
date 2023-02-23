# Generated by Django 4.0.10 on 2023-02-23 20:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('releases', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('followers', models.ManyToManyField(blank=True, related_name='following_fans', to='profiles.profile')),
                ('following_labelbands', models.ManyToManyField(blank=True, related_name='fans', to='releases.labelband')),
            ],
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.profile')),
                ('release', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='releases.release')),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='purchases',
            field=models.ManyToManyField(blank=True, through='profiles.Purchase', to='releases.release'),
        ),
    ]