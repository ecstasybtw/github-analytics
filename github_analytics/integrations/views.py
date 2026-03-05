from django.shortcuts import render
from .services import get_repos, get_user
from django.http import JsonResponse
from django.forms.models import model_to_dict


def sync_user_view(request):
    obj = get_user(request.user)

    data = {
        'name': obj.name,
        'bio': obj.bio,
        'email': obj.email
    }

    return JsonResponse(data)


def sync_repos_view(request):
    dct = get_repos(request.user)

    response = {}

    for repo in dct:
        response[repo.id] = model_to_dict(repo)

    return JsonResponse(response)
