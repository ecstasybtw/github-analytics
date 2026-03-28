from django.urls import path
from .views import profile_view, repo_detail_view, repos_view


urlpatterns = [
    path('profile/', profile_view, name='dashboard-profile'),
    path('repositories/', repos_view, name='dashboard-repositories'),
    path('repo-detail/<int:pk>/', repo_detail_view, name='dashboard_repo_detail'),
]