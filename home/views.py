"""View source file"""

from concurrent.futures import InvalidStateError
import json
import secrets
from subprocess import TimeoutExpired
import requests

from django.shortcuts import render
from django.utils.timezone import now
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.generic.base import TemplateView
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.utils import OperationalError

from oauthlib.oauth2 import WebApplicationClient
from core import settings

from .github_api import request_profile, get_repository
from .models import GitHubRepositoryModel


def request_repository(user, access_token: str, repo_id: int | None = None, repo_owner: str | None = None, repo_name: str | None = None):
    try:
        if repo_owner:
            repo = GitHubRepositoryModel.objects.get(full_name=f'{repo_owner}/{repo_name}').dump()
        else:
            repo = GitHubRepositoryModel.objects.get(id=repo_id).dump()

        if now().timestamp()-repo['cached_at'].timestamp() > settings.CACHE_INVALIDATE:
            raise InvalidStateError()

        print(f"Repo {repo_id} cached!")
        return repo
    except GitHubRepositoryModel.DoesNotExist:
        print(f"Repo {repo_id} not found!")
    except InvalidStateError:
        print(f"Repo {repo_id} invalidated!")
    except OperationalError:
        print(f"Repo Failed to get, no Database connected?")
    if repo_owner:
        repo = get_repository(access_token, repo_owner=repo_owner, repo_name=repo_name)
    elif repo_id:
        repo = get_repository(access_token, repo_id)
    repo = GitHubRepositoryModel(usr=user, repo=repo)
    try:
        repo.save()
    except Exception as e:
        pass
    return repo.dump()


def choose_repo(request):
    if request.method == 'POST':
        repo_id = int(request.POST.get('repo_id'))
        access_token = request.session["access_token"]

        if (repo_id == 0):
            repo_owner = request.POST.get('repo_owner')
            repo_name = request.POST.get('repo_name')
            repo = request_repository(request.user, access_token, repo_owner=repo_owner, repo_name=repo_name)
            return JsonResponse(repo)

        repo = request_repository(request.user, access_token, repo_id)
        return JsonResponse(repo)
        # return JsonResponse({'error': 'Repository not found'})

    return JsonResponse({'error': 'Invalid request'})


def finish_login(request, access_token):
    # print(access_token)
    print('Requesting Profile')
    gh, gh_usr, request.session["profile"] = request_profile(access_token=access_token)
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
