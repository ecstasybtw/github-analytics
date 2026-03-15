from django.urls import path
from .views import profile_view, repo_detail_view


urlpatterns = [
    path('profile/', profile_view, name='dashboard-profile'),
    path('repo-detail/<int:pk>/', repo_detail_view, name='dashboard_repo_detail'),
]