# Generated by Django 4.0.10 on 2023-02-23 21:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
        ('releases', '0001_initial'),
        ('bins', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bin',
            name='releases',
            field=models.ManyToManyField(blank=True, related_name='in_bins', to='releases.release'),
        ),
        migrations.CreateModel(
            name='RecentLabelbandRelease',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recently_released_by', models.ManyToManyField(to='releases.labelband')),
                ('release', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='releases.release')),
            ],
        ),
        migrations.CreateModel(
            name='RecentFanPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recently_bought_by', models.ManyToManyField(to='profiles.profile')),
                ('release', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='releases.release')),
            ],
        ),
    ]