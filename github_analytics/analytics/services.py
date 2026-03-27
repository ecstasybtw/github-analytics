import integrations.models as integration_models
from typing import Any


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



