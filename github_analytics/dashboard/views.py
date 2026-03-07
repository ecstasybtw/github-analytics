from django.shortcuts import render
import integrations.models as integration_models
from django.views.decorators.http import require_GET


@require_GET
def profile_view(request):

    github_user = integration_models.GitHubUser.objects.get(profile_owner=request.user)
    repos = integration_models.GitHubRepo.objects.filter(owner=github_user)
    context = {
        'profile': github_user,
        'repos': repos
    }

    return render(
        request=request,
        template_name='dashboard/profile.html',
        context=context
    )
