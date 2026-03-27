from django.shortcuts import render, redirect, get_object_or_404
from .services import get_repos, get_user, sync_all, _get_metrics, synchronize_repo
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.forms.models import model_to_dict
from django.views.decorators.http import require_POST
from django.contrib import messages
from integrations.models import GitHubRepo, GitHubUser


@require_POST
def sync_user_view(request):
    obj = get_user(request.user)

    data = {
        'name': obj.name,
        'bio': obj.bio,
        'email': obj.email
    }

    return JsonResponse(data)


@require_POST
def sync_repos_view(request):
    dct = get_repos(request.user)

    response = {}

    for repo in dct:
        response[repo.github_repo_id] = model_to_dict(repo)

    return JsonResponse(response)


def sync_all_view(request):
    if request.method == "POST":
        dct = sync_all(request.user)
        messages.success(request, 'Синхронизировано!')
        return redirect('dashboard-profile')

    elif request.method == "GET":
            return render(
                request=request,
                template_name='integrations/synchronize.html'
            )

    else:
        return HttpResponseNotAllowed(["GET", "POST"])

@require_POST
def sync_repo_view(request, repo_pk):
    profile_owner = GitHubUser.objects.get(profile_owner=request.user)
    
    repo_obj = get_object_or_404(GitHubRepo, owner=profile_owner, id=repo_pk)
    synchronize_repo(request.user, repo_obj)
    messages.success(request, 'Синхронизировано!')

    return redirect('dashboard_repo_detail', pk=repo_pk)



