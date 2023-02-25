# Generated by Django 4.0.10 on 2023-02-25 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='labelband',
            name='img_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='labelband',
            name='name',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='labelband',
            name='url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='release',
            name='artist_name',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='release',
            name='img_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='release',
            name='price',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='release',
            name='release_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='release',
            name='title',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='release',
            name='url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='track',
            name='duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='track',
            name='mp3',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='track',
            name='track_number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
