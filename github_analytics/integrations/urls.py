from django.urls import path, include
from .views import sync_repos_view, sync_user_view


urlpatterns = [
    path('sync-user/', sync_user_view, name='integrations_sync_user'),
    path('sync-repos/', sync_repos_view, name='integrations_sync_repos')
]