from django.urls import path

from . import views

urlpatterns = [
    path("profile", views.ProfileView.as_view()),
    path("watchers", views.GetWatchers.as_view()),
    path("watching", views.GetWatching.as_view()),
    path("watch", views.StartWatching.as_view()),
    path("unwatch/<uuid:user_id>", views.StopWatching.as_view()),
    path("watchers/<uuid:user_id>", views.GetWatchersForUserView.as_view()),
    path("watching/<uuid:user_id>", views.GetWatchingForUserView.as_view()),
    path("profile/<uuid:user_id>", views.GetAProfile.as_view()),
    path("skill", views.SkillView.as_view()),
]
