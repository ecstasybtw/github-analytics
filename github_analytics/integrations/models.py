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


class GitHubPullRequest(models.Model):
    pr_owner_login = models.CharField(max_length=128)
    pr_owner_id = models.PositiveBigIntegerField(null=False)
    repo = models.ForeignKey(
        GitHubRepo,
        on_delete=models.CASCADE
    )
    html_url = models.URLField(null=False)
    github_id = models.PositiveBigIntegerField(null=False, unique=True)
    number = models.IntegerField(null=False)
    state = models.CharField(max_length=128)
    locked = models.BooleanField()
    title = models.CharField(max_length=256)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True)
    merged_at = models.DateTimeField(null=True)
    draft = models.BooleanField()
    additions = models.IntegerField()
    deletions = models.IntegerField()
    changed_files = models.IntegerField()
    commits = models.IntegerField()


class GitHubPRReview(models.Model):
    pull_request = models.ForeignKey(
        GitHubPullRequest,
        on_delete=models.CASCADE
    )
    github_id = models.PositiveBigIntegerField(null=False, unique=True)
    reviewer_id = models.PositiveBigIntegerField(null=False)
    reviewer_login = models.CharField(max_length=128)
    body = models.TextField(max_length=512, null=True)
    html_url = models.URLField()
    submitted_at = models.DateTimeField()
    commit_id = models.CharField(max_length=256, null=True)
    state = models.CharField(max_length=64)


class GitHubIssue(models.Model):
    repo = models.ForeignKey(
        GitHubRepo,
        on_delete=models.CASCADE
    )
    github_id = models.PositiveBigIntegerField(null=False, unique=True)
    html_url = models.URLField()
    state = models.CharField(max_length=64)
    title = models.CharField(max_length=256)
    body = models.TextField(max_length=512, null=True)
    author_id = models.PositiveBigIntegerField(null=False)
    author_login = models.CharField(max_length=128)
    closed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    number = models.IntegerField()
    comments = models.IntegerField()
