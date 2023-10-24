# DFB pg. 61
from django.urls import path
from .views import HomePageView, ListProfilesView, AuthorDetailView
from accounts.views import AuthorUpdateView
from . import views  # need this for follow to work 

urlpatterns = [
    path("", HomePageView.as_view(), name="home"), # display HomePageView
    path("authors/", ListProfilesView.as_view(), name="authors_list"), # display list of users on server; is this the exact url they want?
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author_profile"), # display author's profile
    path("authors/<int:pk>/editprofile/", AuthorUpdateView.as_view(), name="author_edit"), # edit user's profile
    path("authors/<int:pk>/followed/", views.follow_author, name="author_followed"), # edit user's profile
    path("authors/my_profile", views.view_my_profile, name="my_profile"), # get all authors on server
]

#TODO are the urls supposed to have a terminating /? Because when I try service/authors/ it gives me a 404. Adding terminating / for now.