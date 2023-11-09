# DFB pg. 165
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from static.vars import ENDPOINT

class AuthorUser(AbstractUser):
    #id - should be generated by db automatically
    uuid = models.CharField(max_length=36, unique=True)
    type = models.CharField(default="author",max_length=6)
    username = models.CharField(max_length=20, unique=True) # https://www.reddit.com/r/django/comments/id2ch0/user_models_username_max_length/
    # change from IP address field to URL field
    host = models.URLField(default = ENDPOINT) # hardcoded localhost for now
    url = models.URLField() #TODO setup proper page
    github = models.URLField(null=True, blank=True)
    profile_image = models.URLField(null=True, blank=True) # optional

    # necessary to edit profile using uuid in url
    slug = models.SlugField(max_length=50, unique=True)
    def save(self, *args, **kwargs):
        self.url = f"{ENDPOINT}authors/{self.uuid}"
        self.slug = self.uuid
        super(AuthorUser, self).save(*args, **kwargs)

class Followers(models.Model):
    author = models.ForeignKey(AuthorUser, on_delete=models.CASCADE, related_name='author', to_field="uuid")
    followers = models.JSONField(default=list)

    def __str__(self): # show summary in django admin view tooltip 
        return self.author.username + "'s " + "Followers"

# This table will delete requests once they have been fulfilled and added to the Follower table
class FollowRequests(models.Model):
    summary = models.CharField(max_length=100)
    # could possible have a boolean for requester and recipient to see if they are local to our node, and instead
    # of storing an entire dictionary of information it can just be an author id which we will retrieve data from in
    # the AuthorUser table. Will see.
    requester_uuid = models.CharField(max_length=36)
    requester = models.JSONField(default=dict)
    recipient_uuid = models.CharField(max_length=36)
    recipient = models.JSONField(default=dict)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): # show summary in django admin view tooltip 
        return self.summary

    # can only request somebody once
    class Meta:
        unique_together = ('requester', 'recipient')