from django.db import IntegrityError, transaction
import requests
from typing import Any
from .models import GitHubUser
try:
    from allauth.socialaccount.models import SocialToken
except Exception:
    SocialToken = None

URL = 'https://api.github.com'
CURRENT_AUTH_USER = '/user'

class GitHubNoTokenException(Exception):
    """Cannot receive user's access token."""

class GitHubUserException(Exception):
    """Cannot get an authenticated user."""

class GitHubJSONException(Exception):
    """Some problems with JSON response from API"""


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


def _request(user, endpoint: str, method: str) -> dict[str, Any] | None:
    token = _get_user_token(user)
    if token:
        headers = _get_headers(token)
        try:
            response = requests.request(url=f'{URL + endpoint}', method=method, headers=headers, timeout=60)
            if response.status_code == 200:
                payload = response.json()
                return payload
            else:
                raise GitHubJSONException
        except (Exception, requests.exceptions.Timeout):
            raise
    else:
        raise GitHubNoTokenException


def get_user(user):
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


