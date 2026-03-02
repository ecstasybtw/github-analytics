import time
from datetime import datetime, timezone
import requests
try:
    from allauth.socialaccount.models import SocialToken
except Exception:
    SocialToken = None

URL = 'https://api.github.com'

class GitHubNoTokenException(Exception):
    """Cannot receive user's access token."""

class GitHubUserException(Exception):
    """Cannot get an authenticated user."""

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

def _get_headers(token):
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def _request(user, endpoint: str, method:str):
    token = _get_user_token(user)
    if token:
        headers = _get_headers(token)
        try:
            response = requests.request(url=f'{URL + endpoint}', method=method, headers=headers)
            payload = response.json()
            return payload
        except Exception:
            return None
    else:
        raise GitHubUserException
