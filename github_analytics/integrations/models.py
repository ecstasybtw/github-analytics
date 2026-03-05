from django.db import models
from django.conf import settings


class GitHubUser(models.Model):
    profile_owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    github_user_id = models.PositiveBigIntegerField(null=False, unique=True)
    login = models.CharField(max_length=128, null=False, unique=True)
    avatar_url = models.URLField()
    name = models.CharField(max_length=128, null=True)
    email = models.EmailField(null=True)
    bio = models.TextField(null=True)


class GitHubRepo(models.Model):
    owner = models.ForeignKey(
        GitHubUser,
        on_delete=models.CASCADE,
    )
    github_repo_id = models.PositiveBigIntegerField(unique=True)
    name = models.CharField(null=False, max_length=256)
    full_name = models.CharField(max_length=256)
    private = models.BooleanField()
    html_url = models.URLField(null=False)
    description = models.TextField(null=True)
    language = models.CharField(max_length=64, null=True)
    archived = models.BooleanField()
    forks_count = models.IntegerField()
    stargazers_count = models.IntegerField()
    open_issues_count = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    pushed_at = models.DateTimeField()
