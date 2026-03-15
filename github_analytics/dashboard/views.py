from django.shortcuts import render
import integrations.models as integration_models
from integrations.services import _get_metrics
from django.views.decorators.http import require_GET


@require_GET
def profile_view(request):

    github_user = integration_models.GitHubUser.objects.get(profile_owner=request.user)
    repos = integration_models.GitHubRepo.objects.filter(owner=github_user).order_by('-updated_at', 'name')
    metrics = _get_metrics(request.user)

    context = {
        'profile': github_user,
        'repos': repos,
        'metrics': metrics
    }

    return render(
        request=request,
        template_name='dashboard/profile.html',
        context=context
    )

def repo_detail_view(request, pk):
    repo = integration_models.GitHubRepo.objects.get(id=pk)

    context = {
        'repo': repo
    }

    return render(request, 'dashboard/repo_detail.html', context=context)
