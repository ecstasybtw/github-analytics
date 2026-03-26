from django.db import IntegrityError, transaction
from django.utils.dateparse import parse_datetime
from django.forms.models import model_to_dict
import requests
from typing import Any
from .models import GitHubUser, GitHubRepo, GitHubPullRequest, GitHubPRReview, GitHubIssue
try:
    from allauth.socialaccount.models import SocialToken
except Exception:
    SocialToken = None


URL = 'https://api.github.com'
CURRENT_AUTH_USER = '/user'
CURRENT_AUTH_USER_REPOS = '/user/repos'


def _build_repo_endpoint(owner, repo, review=False, pull_number=None, issues=False, single_repo=False):
    if review:
        return f'/repos/{owner}/{repo}/pulls/{pull_number}/reviews'

    if issues:
        return f'/repos/{owner}/{repo}/issues'

    if single_repo:
        return f'/repos/{owner}/{repo}'

    return f'/repos/{owner}/{repo}/pulls'


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


def _get_pr_params(
        state:str = 'all',
        head:str = None,
        base:str = None,
        sort:str = 'created',
        direction:str = 'desc',
        per_page:int = 30,
        page:int = 1
) -> dict[str, Any]:

    params = {
        'state': state,
        'head': head,
        'base': base,
        'sort': sort,
        'direction': direction,
        'per_page': per_page,
        'page': page
    }

    filtered_params = {
        key: value for key, value in params.items() if value is not None
    }

    return filtered_params


def _get_reviews_params(
        per_page:int = 30,
        page:int = 1
):

    return {
        'per_page': per_page,
        'page': page
    }


def _get_issues_params(
        milestone:str = None,
        state:str = 'all',
        assignee:str = None,
        type:str = None,
        creator:str = None,
        mentioned:str = None,
        labels:list[Any] = None,
        sort:str = 'created',
        direction:str = 'desc',
        since:str = None,
        per_page:int = 30,
        page:int = 1
) -> dict[str, Any]:

    params = {
        'milestone' : milestone,
        'state': state,
        'assignee': assignee,
        'type': type,
        'creator': creator,
        'mentioned': mentioned,
        'labels': labels,
        'sort': sort,
        'direction': direction,
        'since': since,
        'per_page': per_page,
        'page': page
    }

    filtered_params = {
        key: value for key, value in params.items() if value is not None
    }

    return filtered_params


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
        payload = _request(
            user=user,
            endpoint=CURRENT_AUTH_USER,
            method='GET'
        )
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


def _upsert_repo_from_payload(repo_payload, github_owner):
    with transaction.atomic():
        github_repo_id = repo_payload['id']

        obj, created = GitHubRepo.objects.update_or_create(
            github_repo_id=github_repo_id,
            defaults={
                'owner': github_owner,
                'github_owner_id': repo_payload['owner']['id'],
                'github_owner_login': repo_payload['owner']['login'],
                'name': repo_payload['name'],
                'full_name': repo_payload['full_name'],
                'private': repo_payload['private'],
                'html_url': repo_payload['html_url'],
                'description': repo_payload['description'],
                'language': repo_payload['language'],
                'archived': repo_payload['archived'],
                'forks_count': repo_payload['forks_count'],
                'stargazers_count': repo_payload['stargazers_count'],
                'open_issues_count': repo_payload['open_issues_count'],
                'created_at': parse_datetime(repo_payload['created_at']) if repo_payload['created_at'] else None,
                'updated_at': parse_datetime(repo_payload['updated_at']) if repo_payload['updated_at'] else None,
                'pushed_at': parse_datetime(repo_payload['pushed_at']) if repo_payload['pushed_at'] else None
            }
        )

    return obj, created


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
        payload = _request(
            user=user,
            endpoint=CURRENT_AUTH_USER_REPOS,
            params=params, method='GET'
        )
    except (GitHubNoTokenException, GitHubJSONException):
        raise

    if payload:
        dct = []
        github_owner = GitHubUser.objects.get(profile_owner=user)
        for repo in payload:
            obj, created = _upsert_repo_from_payload(
                repo_payload=repo,
                github_owner=github_owner
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


def _get_pull_requests(user, repo: GitHubRepo):
    params = _get_pr_params()

    try:
        payload = _request(
            user=user,
            endpoint=_build_repo_endpoint(
                owner=repo.github_owner_login,
                repo=repo.name
            ),
            params=params,
            method='GET'
        )
    except (GitHubNoTokenException, GitHubJSONException):
        raise

    if payload:
        dct = []

        with transaction.atomic():
            for pr in payload:
                github_pr_id = pr['id']

                obj, created = GitHubPullRequest.objects.update_or_create(
                    github_id=github_pr_id,
                    defaults={
                        'pr_owner_login': pr['user']['login'],
                        'pr_owner_id': pr['user']['id'],
                        'repo': repo,
                        'html_url': pr['html_url'],
                        'number': pr['number'],
                        'state': pr['state'],
                        'locked': pr['locked'],
                        'title': pr['title'],
                        'created_at': parse_datetime(pr['created_at']) if pr['created_at'] else None,
                        'updated_at': parse_datetime(pr['updated_at']) if pr['updated_at'] else None,
                        'closed_at': parse_datetime(pr['closed_at']) if pr['closed_at'] else None,
                        'merged_at': parse_datetime(pr['merged_at']) if pr['merged_at'] else None,
                        'draft': pr['draft'],
                        'additions': pr['additions'],
                        'deletions': pr['deletions'],
                        'changed_files': pr['changed_files'],
                        'commits': pr['commits']
                    }
                )

                dct.append(obj)

        return dct

    return []


def _get_reviews(user, pull_request: GitHubPullRequest, repo: GitHubRepo):
    params = _get_reviews_params()

    try:
        payload = _request(
            user=user,
            endpoint=_build_repo_endpoint(
                owner=repo.github_owner_login,
                repo=repo.name,
                review=True,
                pull_number=pull_request.number
            ),
            params=params,
            method='GET'
        )
    except (GitHubNoTokenException, GitHubJSONException):
        raise

    if payload:
        dct = []

        with transaction.atomic():
            for review in payload:
                github_id = review['id']

                obj, created = GitHubPRReview.objects.update_or_create(
                    pull_request=pull_request,
                    github_id=github_id,
                    defaults={
                        'reviewer_id': review['user']['id'],
                        'reviewer_login': review['user']['login'],
                        'body': review['body'],
                        'html_url': review['html_url'],
                        'submitted_at': parse_datetime(review['submitted_at']) if review['submitted_at'] else None,
                        'commit_id': review['commit_id'],
                        'state': review['state']
                    }
                )

                dct.append(obj)

        return dct

    return []


def _get_issues(user, repo: GitHubRepo):
    params = _get_issues_params()

    try:
        payload = _request(
            user=user,
            endpoint=_build_repo_endpoint(
                owner=repo.github_owner_login,
                repo=repo.name,
                issues=True
            ),
            params=params,
            method='GET'
        )
    except (GitHubNoTokenException, GitHubJSONException):
        raise

    if payload:
        dct = []
        with transaction.atomic():
            for issue in payload:
                github_id = issue['id']

                obj, created = GitHubIssue.objects.update_or_create(
                    github_id=github_id,
                    defaults={
                        'repo': repo,
                        'html_url': issue['html_url'],
                        'state': issue['state'],
                        'title': issue['title'],
                        'body': issue['body'],
                        'author_id': issue['user']['id'],
                        'author_login': issue['user']['login'],
                        'closed_at': parse_datetime(issue['closed_at']) if issue['closed_at'] else None,
                        'created_at': parse_datetime(issue['created_at']) if issue['created_at'] else None,
                        'updated_at': parse_datetime(issue['updated_at']) if issue['updated_at'] else None,
                        'number': issue['number'],
                        'comments': issue['comments']
                    }
                )

                dct.append(obj)

        return dct

    return []


def synchronize_repo(user, repo_obj: GitHubRepo) -> dict[Any, Any]:
    try:
        repo = _request(
            user=user,
            endpoint=_build_repo_endpoint(
                owner=repo_obj.github_owner_login,
                repo=repo_obj.name,
                single_repo=True
            ),
            method='GET'
        )

    except (GitHubNoTokenException, GitHubJSONException):
        raise

    if repo:

        github_owner = GitHubUser.objects.get(profile_owner=user)

        obj, created = _upsert_repo_from_payload(
            repo_payload=repo,
            github_owner=github_owner
        )

        pull_requests = _get_pull_requests(user=user, repo=obj)
        pull_requests_count = len(pull_requests)

        reviews_count = 0
        for request in pull_requests:
           reviews_count += len(_get_reviews(user=user, pull_request=request, repo=obj))
        issues_count = len(_get_issues(user=user, repo=obj))

        return {
            'repo': obj,
            'pull_requests_count': pull_requests_count,
            'issues_count': issues_count,
            'reviews_count': reviews_count
        }

    return {}




