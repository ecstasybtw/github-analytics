import integrations.models as integration_models
from typing import Any
from django.db.models import Avg


def get_basic_metrics(repo: integration_models.GitHubRepo) -> dict[Any, Any]:
    prs = (
        integration_models.GitHubPullRequest.objects
        .filter(repo=repo)
    )

    total_prs = (
        prs
        .all()
        .count()
    )

    open_prs = (
        prs.
        filter(state='open').
        all().
        count()
    )

    merged_prs = (
        prs
        .filter(merged_at__isnull=False)
        .count()
    )

    closed_prs = (
        prs
        .filter(state='closed')
        .count()
    )

    total_reviews = (
        integration_models.GitHubPRReview.objects
        .filter(pull_request__in=prs)
        .count()
    )

    reviewed_prs = (
        prs
        .filter(
            reviews__isnull=False
        )
        .distinct()
        .count()
    )

    avg_reviews_per_pr = total_reviews / total_prs if total_prs != 0 else 0

    return {
        'total_prs': total_prs,
        'open_prs': open_prs,
        'merged_prs': merged_prs,
        'closed_prs': closed_prs,
        'total_reviews': total_reviews,
        'reviewed_prs': reviewed_prs,
        'avg_reviews_per_pr': avg_reviews_per_pr
    }


def get_basic_issues_metrics(repo: integration_models.GitHubRepo) -> dict[Any, Any]:
    issues = (
        integration_models.GitHubIssue
        .objects
        .filter(
            repo=repo
        )
    )

    total_issues = (
        issues
        .all()
        .count()
    )

    open_issues = (
        issues
        .filter(
            state='open'
        )
        .count()
    )

    closed_issues = (
        issues
        .filter(
            state='closed'
        )
        .count()
    )

    issues_with_comments = (
        issues
        .filter(
            comments__gt=0
        )
        .count()
    )

    avg_comments_per_issue = (
        issues.aggregate(
            Avg('comments')
        )['comments__avg']
    )

    return {
        'total_issues': total_issues,
        'open_issues': open_issues,
        'closed_issues': closed_issues,
        'issues_with_comments': issues_with_comments,
        'avg_comments_per_issue': avg_comments_per_issue if avg_comments_per_issue else 0
    }



