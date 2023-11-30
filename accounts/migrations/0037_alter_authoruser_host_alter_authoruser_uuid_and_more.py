# Generated by Django 4.2.6 on 2023-11-28 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0036_alter_authoruser_host_alter_authoruser_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authoruser',
            name='host',
            field=models.URLField(default='http://localhost:8000/'),
        ),
        migrations.AlterField(
            model_name='authoruser',
            name='uuid',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='followrequests',
            name='recipient_uuid',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='followrequests',
            name='requester_host',
            field=models.CharField(max_length=350, null=True),
        ),
        migrations.AlterField(
            model_name='followrequests',
            name='requester_url',
            field=models.CharField(max_length=350, null=True),
        ),
        migrations.AlterField(
            model_name='followrequests',
            name='requester_uuid',
            field=models.CharField(max_length=50),
        ),
    ]