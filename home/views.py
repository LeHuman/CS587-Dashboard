"""View source file"""

import json
import secrets
import requests

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.generic.base import TemplateView
from django.contrib.auth import login, logout
from django.contrib import messages

from oauthlib.oauth2 import WebApplicationClient
from core import settings

from .github_api import request_profile, get_repository
from .models import GitHubRepositoryModel


def request_repository(user, access_token: str, repo_id: int):
    try:
        repo = GitHubRepositoryModel.objects.get(id=repo_id).dump()
        print(f"Repo {repo_id} cached!")
        return repo
    except GitHubRepositoryModel.DoesNotExist:
        pass
    print(f"Repo {repo_id} not found!")
    repo = get_repository(access_token, repo_id)
    repo = GitHubRepositoryModel(user=user, repo=repo)
    repo.save()
    return repo.dump()


def choose_repo(request):
    if request.method == 'POST':
        repo_id = request.POST.get('repo_id')

        try:
            repo_id = int(repo_id)
            access_token = request.session["access_token"]

            repo = request_repository(request.user, access_token, repo_id)

            return JsonResponse(repo)

        except Exception as e:
            raise e
            return JsonResponse({'error': 'Repository not found'})

    return JsonResponse({'error': 'Invalid request'})


def finish_login(request, access_token):
    # print(access_token)
    print('Requesting Profile')
    gh, gh_usr, request.session["profile"] = request_profile(access_token=access_token)
    print(gh_usr.owned_private_repos_count)
    print(gh_usr.total_private_repos_count)
    print('Done')
    try:
        # IMPROVE: update periodically, instead on each logon
        user = User.objects.get(username=gh_usr.login)
        usr_str = f"User {user.username} already exists, Authenticated {user.is_authenticated}"
        print(usr_str)
        login(request, user)

    except Exception as e:
        print(f"ERROR: {e}")
        user = User.objects.create_user(gh_usr.login)
        usr_str = f"User {user.username} is created, Authenticated {user.is_authenticated}?"
        print(usr_str)
        login(request, user)


def github_login(request):
    """Contact GitHub to authenticate"""

    if settings.CURRENT_TOKEN:
        finish_login(request, settings.CURRENT_TOKEN)
        request.session["access_token"] = settings.CURRENT_TOKEN
        return HttpResponseRedirect(reverse("home:index"))

    # Setup a Web Application Client from oauthlib
    client_id = settings.GITHUB_OAUTH_CLIENT_ID
    client = WebApplicationClient(client_id)

    # Store state info in session
    request.session["state"] = secrets.token_urlsafe(16)

    uri = request.build_absolute_uri('/')[:-1].strip("/")

    url = client.prepare_request_uri(
        settings.GITHUB_OAUTH_URL,
        redirect_uri=f"{uri}/{settings.GITHUB_OAUTH_CALLBACK_URL}",
        scope=settings.GITHUB_OAUTH_SCOPES,
        state=request.session["state"],
        allow_signup="false",
    )

    # Redirect to the complete authorization url
    return HttpResponseRedirect(url)


def logout_request(request):
    """Request view to log out"""
    logout(request)
    # messages.add_message(request, messages.SUCCESS, "You are successfully logged out")
    return HttpResponseRedirect(reverse("home:index"))


def index(request):
    """Default view"""
    items = {'username': request.user.username, 'auth': request.user.is_authenticated}
    items_json = json.dumps(items)

    if request.user.is_authenticated:
        context = {'items': items_json}
    else:
        context = {}

    return render(request, 'pages/index.html', context)
    # return render(request, 'pages/index.html')


class CallbackView(TemplateView):
    """Client Callback from GitHub"""

    # def post(self, request, *args, **kwargs):
    #     print(request)

    # def show_repositories(self, request, *args, **kwargs):
    #     # Retrieve models based on the date range (you need to define your date range logic)
    #     start_date = self.request.GET.get('start_date', None)
    #     end_date = self.request.GET.get('end_date', None)
    #     repositories = GitHubRepositoryModel.objects.filter(created_at__range=(start_date, end_date))
    #     print(request)

    #     # Pass the repositories and the date range form to the template context
    #     form = DateRangeForm()  # Instantiate the date range form
    #     context = {
    #         'user_repositories': repositories,
    #         'form': form,
    #     }

    #     return render(request, 'index.html', context)

    def get(self, request, *args, **kwargs):
        # Retrieve these data from the URL
        data = self.request.GET

        if "error" in data:
            print(self.request.GET["error"])
            return HttpResponseRedirect(reverse("home:index"))

        code = data["code"]
        state = data["state"]

        # For security purposes, verify that the
        # state information is the same as was passed
        # to github_login()
        if self.request.session["state"] != state:
            messages.add_message(self.request, messages.ERROR, "State information mismatch!")
            return HttpResponseRedirect(reverse("home:index"))
        else:
            del self.request.session["state"]

        # fetch the access token from GitHub's API at token_url
        token_url = "https://github.com/login/oauth/access_token"
        client_id = settings.GITHUB_OAUTH_CLIENT_ID
        client_secret = settings.GITHUB_OAUTH_SECRET

        # Create a Web Application Client from oauthlib
        client = WebApplicationClient(client_id)

        uri = request.build_absolute_uri('/')[:-1].strip("/")

        # Prepare body for request
        data = client.prepare_request_body(
            code=code,
            redirect_uri=f"{uri}/{settings.GITHUB_OAUTH_CALLBACK_URL}",
            client_id=client_id,
            client_secret=client_secret,
        )

        # Post a request at GitHub's token_url
        # Returns requests.Response object
        response = requests.post(token_url, data=data, timeout=5000)  # TODO: handle timeout
        client.parse_request_body_response(response.text)
        access_token = client.token["access_token"]
        self.request.session["access_token"] = access_token

        finish_login(self.request, access_token)

        # Redirect response to hide the callback url in browser
        return HttpResponseRedirect(reverse("home:index"))
