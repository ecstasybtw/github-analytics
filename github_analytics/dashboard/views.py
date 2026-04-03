from django.shortcuts import render, redirect, get_object_or_404
import integrations.models as integration_models
from integrations.services import _get_metrics
from django.views.decorators.http import require_GET
from analytics.services import get_basic_metrics, get_basic_issues_metrics, basic_comparison


@require_GET
def profile_view(request):
    github_user = integration_models.GitHubUser.objects.get(profile_owner=request.user)

    context = {
        'profile': github_user,
    }

    return render(
        request=request,
        template_name='dashboard/profile.html',
        context=context
    )

@require_GET
def repos_view(request):
    github_user = integration_models.GitHubUser.objects.get(profile_owner=request.user)
    filter_param = request.GET.get('visibility')
    affiliation_param = request.GET.get('affiliation')
    active_repo_filter = 'all'

    repos = integration_models.GitHubRepo.objects.filter(owner=github_user).order_by('-updated_at', 'name')
    metrics = _get_metrics(request.user)

    if filter_param == 'private':
        repos = repos.filter(private=True)
        active_repo_filter = 'private'
    elif filter_param == 'public':
        repos = repos.filter(private=False)
        active_repo_filter = 'public'

    if affiliation_param == 'collaborator':
        repos = repos.exclude(github_owner_id=github_user.github_user_id)
        active_repo_filter = 'collaborator'

    context = {
        'repos': repos,
        'metrics': metrics,
        'active_repo_filter': active_repo_filter,
    }

    return render(
        request=request,
        template_name='dashboard/repositories.html',
        context=context
    )


def repo_detail_view(request, pk):
    profile_owner = integration_models.GitHubUser.objects.get(profile_owner=request.user)

    repo = get_object_or_404(integration_models.GitHubRepo, owner=profile_owner, id=pk)


    basic_metrics = get_basic_metrics(repo)
    basic_issues_metrics = get_basic_issues_metrics(repo)
    basic_comparison_metrics = basic_comparison(
        basic_metrics=basic_metrics,
        basic_issues_metrics=basic_issues_metrics
    )

    context = {
        'repo': repo,
        'basic_metrics': basic_metrics,
        'basic_issues_metrics': basic_issues_metrics,
        'basic_comparison_metrics': basic_comparison_metrics
    }

    return render(request, 'dashboard/repo_detail.html', context=context)


def landing_view(request):

    context = {
        'landing': True
    }

    if request.user.is_authenticated:
        return redirect('dashboard-profile')

    else:
        return render(request, 'dashboard/login.html', context=context)

