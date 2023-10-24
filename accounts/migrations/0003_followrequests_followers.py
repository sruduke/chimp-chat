# Generated by Django 4.2.6 on 2023-10-16 22:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_remove_authoruser_age_authoruser_github_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FollowRequests',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('summary', models.CharField(max_length=100)),
                ('requester', models.JSONField(default=dict)),
                ('recipient', models.JSONField(default=dict)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'unique_together': {('requester', 'recipient')},
            },
        ),
        migrations.CreateModel(
            name='Followers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('followers', models.JSONField(default=list)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='author', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]