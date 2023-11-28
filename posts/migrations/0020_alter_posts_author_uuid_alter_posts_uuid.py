# Generated by Django 4.2.6 on 2023-11-27 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0019_likes_liked_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='posts',
            name='author_uuid',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='posts',
            name='uuid',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, unique=True),
        ),
    ]