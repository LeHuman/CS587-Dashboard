"""View source file"""

import json
import secrets
import github3
import requests

# from github import Github
# from github import Auth

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.generic.base import TemplateView
from django.contrib.auth import login, logout
from django.contrib import messages
from oauthlib.oauth2 import WebApplicationClient
from github3.users import ShortUser
from github3.repos import ShortRepository
from github3.events import Event

from core import settings
from home.github_api import get_user

def github_login(request):
    """Contact GitHub to authenticate"""
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
    messages.add_message(request, messages.SUCCESS, "You are successfully logged out")
    return render(request, "pages/index.html")

def index(request):
    """Default view to log out"""
    # Page from the theme
    return render(request, 'pages/index.html')

class CallbackView(TemplateView):
    """Client Callback from GitHub"""

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
        response = requests.post(token_url, data=data, timeout=5000) # TODO: handle timeout

        client.parse_request_body_response(response.text)

        access_token = client.token["access_token"]

        # Prepare an Authorization header for GET request using the 'access_token' value
        # using GitHub's official API format
        # header = {"Authorization": f"token {access_token}"}

        # Retrieve GitHub profile data
        # Send a GET request
        # Returns requests.Response object
        # response = requests.get("https://api.github.com/user", headers=header, timeout=5000) # TODO: handle timeout

        # Store profile data in JSON
        # json_dict = response.json()

        # save the user profile in a session
        # self.request.session["json_profile"] = json_dict

        # auth = Auth.Token(access_token)
        # g = Github(auth=auth)
        # me = g.get_user()
        # user_profile = {
        #     "login" : me.login,
        #     "email" : me.email,
        #     "repos" : [x for x in me.get_repos()],
        #     "starred" : [x for x in me.get_starred()],
        # }
        # g.close()

        # print(user_profile)

        def str_short_user(usr : ShortUser) -> dict[str,str]:
            return {
                "id":usr.id,
                "login" : usr.login,
                "avatar_url" : usr.avatar_url,
                "url":usr.html_url,
            }

        def str_event(event : Event) -> dict[str,str]:
            return {
                "actor" : event.actor.id,
                "created_at" : event.created_at.strftime("%d/%m/%Y, %H:%M:%S") if event.created_at else "None",
                "id" : event.id,
                "org" : event.org.id if event.org else "None",
                "type" : event.type,
                "payload" : event.payload,
                "repo" : event.repo,
                "public" : event.public,
            }

        def str_short_repository(repo : ShortRepository) -> dict[str,str]:
            return {
                "id":repo.id,
                "name" : repo.name,
                "full_name" : repo.full_name,
                "description" : repo.description,
                "created_at" : repo.created_at,
                "updated_at" : repo.updated_at,
                "homepage" : repo.homepage,
                "language" : repo.language,
                "archived" : repo.archived,
                "fork" : repo.fork,
                "open_issues" : repo.open_issues,
                "watchers" : repo.watchers,
                "url":repo.html_url,
            }

        gh_usr = get_user(token=access_token)
        self.request.session["profile"] = {
            "id" : gh_usr.id,
            "name" : gh_usr.name,
            "login" : gh_usr.login,
            "avatar_url" : gh_usr.avatar_url,
            "url" : gh_usr.html_url,
            "email" : gh_usr.email,
            "followers" : [str_short_user(x) for x in gh_usr.followers(10)],
            "following" : [str_short_user(x) for x in gh_usr.following(10)],
            "bio" : gh_usr.bio,
            "company" : gh_usr.company,
            "events" : [str_event(x) for x in gh_usr.events(True, 10)],
            "starred_repos" : [str_short_repository(x) for x in gh_usr.starred_repositories(sort='updated', number=10)],
            "subscriptions" : [str_short_repository(x) for x in gh_usr.subscriptions(number=10)],
            "plan" : gh_usr.plan,
            "follower_count" : gh_usr.followers_count,
            "repo_pub_count" : gh_usr.public_repos_count,
            "repo_priv_count" : gh_usr.total_private_repos_count if gh_usr.total_private_repos_count else 0,
            "gist_pub_count" : gh_usr.public_gists_count if gh_usr.public_gists_count else 0,
            "repos" : [str_short_repository(x) for x in gh_usr._iter(10, gh_usr.repos_url, ShortRepository, {"sort": 'created', "direction": 'desc'})],
            "api_limit" : gh_usr.ratelimit_remaining,
        }

        # print(f"Ratelimit remaining:{gh_usr.ratelimit_remaining}")

        # print(json.dumps(self.request.session["profile"], indent=4))

        # gh_user = get_user(token=access_token) # TODO: handle get_user error
        # print(gh_user.login)
        # self.request.session["login"] = gh_user.login
        # self.request.session["email"] = gh_user.email
        # self.request.session["avatar_url"] = gh_user.avatar_url
        # self.request.session["followers"] = [gh_user.followers()]
        # self.request.session["starred_repos"] = [gh_user.starred_repositories()]
        # self.request.session["last_modified"] = [gh_user.last_modified]

        # retrieve or create a Django User for this profile
        try:
            user = User.objects.get(username=gh_usr.login)
            usr_str = f"User {user.username} already exists, Authenticated {user.is_authenticated}"

            messages.add_message(self.request, messages.DEBUG, usr_str)
            print(usr_str)

            # remember to log the user into the system
            login(self.request, user)

        except Exception:
            # create a Django User for this login
            user = User.objects.create_user(gh_usr.login, gh_usr.email)
            usr_str = f"User {user.username} is created, Authenticated {user.is_authenticated}?"

            messages.add_message(self.request, messages.DEBUG, usr_str)
            print(usr_str)

            # remember to log the user into the system
            login(self.request, user)

        # Redirect response to hide the callback url in browser
        return HttpResponseRedirect(reverse("home:index"))
