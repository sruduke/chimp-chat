# DFB pg. 165
from django.contrib.auth.models import AbstractUser
from django.db import models

class AuthorUser(AbstractUser):
    #id - should be generated by db automatically
    username = models.CharField(max_length=20, unique=True) # https://www.reddit.com/r/django/comments/id2ch0/user_models_username_max_length/
    host = models.GenericIPAddressField(default = "http://127.0.0.1:8000/") # hardcoded localhost for now
    url = models.URLField() #TODO setup proper page
    github = models.URLField()
    profile_image = models.URLField() #TODO don't know what this should be