# Generated by Django 4.2.7 on 2024-10-07 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='otpverification',
            name='user',
        ),
        migrations.AddField(
            model_name='otpverification',
            name='mobile',
            field=models.TextField(blank=True, null=True),
        ),
    ]