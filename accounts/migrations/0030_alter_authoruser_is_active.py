# Generated by Django 4.2.6 on 2023-11-13 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0029_alter_whitelistcontroller_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authoruser',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
