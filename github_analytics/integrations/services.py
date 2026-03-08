from django.db import IntegrityError, transaction
from django.utils.dateparse import parse_datetime
from django.forms.models import model_to_dict
import requests
from typing import Any
from .models import GitHubUser, GitHubRepo
try:
    from allauth.socialaccount.models import SocialToken
except Exception:
    SocialToken = None


URL = 'https://api.github.com'
CURRENT_AUTH_USER = '/user'
CURRENT_AUTH_USER_REPOS = '/user/repos'


class GitHubNoTokenException(Exception):
    """Cannot receive user's access token."""

class GitHubUserException(Exception):
    """Cannot get an authenticated user."""

class GitHubJSONException(Exception):
    """Some problems with JSON response from API."""

class GitHubNoReposException(Exception):
    """User does not have any repos."""


def _get_user_token(user):
    if SocialToken is None or not user.is_authenticated:
        return None

    try:
        token = (
            SocialToken.objects.select_related('account')
            .get(account__user=user, account__provider='github')
        )
        return token.token

    except SocialToken.DoesNotExist:
        return None


def _get_headers(token) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_repo_params(
        type:str = 'all',
        sort: str = 'full_name',
        direction: str = 'asc',
        per_page: int = 30,
        page: int = 1,
) -> dict[str, Any]:

    params = {
        'type': type,
        'sort': sort,
        'direction': direction,
        'per_page': per_page,
        'page': page
    }

    return params


def _request(user, endpoint: str, method: str, params: dict[Any, Any] | None = None) -> dict[Any, Any] | None:
    token = _get_user_token(user)
    if token:
        headers = _get_headers(token)
        try:
            response = requests.request(url=f'{URL + endpoint}', method=method, headers=headers, params=params, timeout=60)
            if response.status_code == 200:
                payload = response.json()
                return payload
            else:
                raise GitHubJSONException
        except (Exception, requests.exceptions.Timeout):
            raise
    else:
        raise GitHubNoTokenException


def get_user(user) -> GitHubUser | None:
    try:
        payload = _request(user=user, endpoint=CURRENT_AUTH_USER, method='GET')
    except (GitHubNoTokenException, GitHubJSONException):
        raise

    if payload:
        with transaction.atomic():
            obj, created = GitHubUser.objects.update_or_create(
                github_user_id=payload['id'],
                defaults={
                    'profile_owner': user,
                    'github_user_id': payload['id'],
                    'login': payload['login'],
                    'avatar_url': payload['avatar_url'],
                    'name': payload['name'],
                    'email': payload['email'],
                    'bio': payload['bio']
                }
            )
            return obj

    return None


def get_repos(
        user,
        type: str = 'all',
        sort: str = 'full_name',
        direction: str = 'asc',
        per_page: int = 30,
        page: int = 1,
) -> list[GitHubRepo]:
    params = _get_repo_params(
        type=type,
        sort=sort,
        direction=direction,
        per_page=per_page,
        page=page
    )

    try:
        payload = _request(user=user, endpoint=CURRENT_AUTH_USER_REPOS, params=params, method='GET')
    except (GitHubNoTokenException, GitHubJSONException):
        raise

    if payload:
        dct = []
        github_owner = GitHubUser.objects.get(profile_owner=user)
        with transaction.atomic():
            for repo in payload:
                github_repo_id = repo['id']

                obj, created = GitHubRepo.objects.update_or_create(
                    github_repo_id=github_repo_id,
                    defaults={
                        'owner': github_owner,
                        'name': repo['name'],
                        'full_name': repo['full_name'],
                        'private': repo['private'],
                        'html_url': repo['html_url'],
                        'description': repo['description'],
                        'language': repo['language'],
                        'archived': repo['archived'],
                        'forks_count': repo['forks_count'],
                        'stargazers_count': repo['stargazers_count'],
                        'open_issues_count': repo['open_issues_count'],
                        'created_at': parse_datetime(repo['created_at']) if repo['created_at'] else None,
                        'updated_at': parse_datetime(repo['updated_at']) if repo['updated_at'] else None,
                        'pushed_at': parse_datetime(repo['pushed_at']) if repo['pushed_at'] else None
                    }
                )

                dct.append(obj)

        return dct

    return []

def sync_all(user):
    try:
        user_obj = get_user(user)
    except GitHubNoTokenException:
        raise

    try:
        repos_obj = get_repos(user)
    except GitHubNoTokenException:
        raise

    dct = {
        user_obj.github_user_id: [
            model_to_dict(item) for item in repos_obj
        ]
    }

    return dct


def _get_metrics(user):
    try:
        github_profile = GitHubUser.objects.get(profile_owner=user)
    except GitHubUser.DoesNotExist:
        raise

    repos = GitHubRepo.objects.filter(owner=github_profile).order_by('-pushed_at')

    repos_count = repos.count()
    stars_count = sum(repo.stargazers_count for repo in repos)
    forks_count = sum(repo.forks_count for repo in repos)
    open_issues_count = sum(repo.open_issues_count for repo in repos)

    last_updated_repo = repos.first()
    if last_updated_repo:
        last_pushed_repo_at = last_updated_repo.updated_at
    else:
        last_pushed_repo_at = None


    return {
        'repos_count': repos_count,
        'stars_count': stars_count,
        'forks_count': forks_count,
        'open_issues_count': open_issues_count,
        'last_pushed_repo_at': last_pushed_repo_at
    }







