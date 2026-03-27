from django.urls import path, include
from .views import sync_repos_view, sync_user_view, sync_all_view, sync_repo_view


urlpatterns = [
    path('sync-user/', sync_user_view, name='integrations_sync_user'),
    path('sync-repos/', sync_repos_view, name='integrations_sync_repos'),
    path('sync-all/', sync_all_view, name='integrations_sync_all'),
    path('sync-repo/<int:repo_pk>/', sync_repo_view, name='integrations_sync_repo')
]