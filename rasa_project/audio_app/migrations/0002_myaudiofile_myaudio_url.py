# Generated by Django 5.0.7 on 2024-09-11 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audio_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='myaudiofile',
            name='myaudio_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
