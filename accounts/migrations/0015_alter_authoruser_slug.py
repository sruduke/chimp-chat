# Generated by Django 4.2.6 on 2023-11-08 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_authoruser_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authoruser',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
