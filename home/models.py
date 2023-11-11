from datetime import datetime
import json
from time import sleep
from typing import Callable
import concurrent.futures

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import make_aware, now, utc

from github3 import GitHub, login
import github3
from github3.exceptions import ForbiddenError
from github3.users import AuthenticatedUser
from github3.users import ShortUser
from github3.events import Event
from github3.repos import Repository
from github3.repos.branch import Branch
from github3.structs import GitHubIterator

from .github_api import str_short_user, str_short_pull_request


def get_gh_datetime(dt: str | datetime | None) -> datetime:
    if isinstance(dt, datetime):
        return dt
    if isinstance(dt, str):
        try:
            return make_aware(datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ"))
        except ValueError as e:
            print(e)
    return datetime(0, 0, 0)


def iter_long(gi: Callable, *args, **kwargs) -> list:
    it = gi(*args, **kwargs)
    fnl = list(it)
    while it.last_status == 202:
        print('Waiting for 202')
        sleep(3)  # IMPROVE: sleeping
        it = gi(*args, **kwargs)
        fnl = list(it)
    # print(fnl)
    return fnl


class GitHubRepositoryModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.IntegerField(primary_key=True)  # IMPROVE: Only works in context of GitHub
    cached_at = models.DateTimeField(default=datetime.utcfromtimestamp(0).replace(tzinfo=utc))
    owner = models.JSONField(default=dict)
    private = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=512)
    description = models.CharField(max_length=1024)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    homepage = models.URLField()
    language = models.CharField(max_length=255)
    archived = models.BooleanField()
    forks_count = models.IntegerField()
    open_issues_count = models.IntegerField(default=0)
    pull_requests_count = models.IntegerField(default=0)
    pull_requests = models.JSONField(default=list)
    watchers_count = models.IntegerField()
    url = models.URLField()
    collaborators = models.JSONField(default=list)
    collaborators_access = models.BooleanField(default=False)
    commit_activity = models.JSONField(default=list)
    commits = models.JSONField(default=list)
    code_freq = models.JSONField(default=list)
    branches = models.JSONField(default=list)
    branch_count = models.IntegerField(default=1)

    def __init__(self,  usr: User, _id=None, cached_at=None, owner=None, private=None, name=None, full_name=None, description=None, created_at=None, updated_at=None, homepage=None,
                 language=None, archived=None, forks_count=None, open_issues_count=None, pull_requests_count=None, pull_requests=None, watchers_count=None, url=None, collaborators=None, collaborators_access=None, commit_activity=None,
                 commits=None, code_freq=None, branches=None, branch_count=None, repo: Repository | None = None):
        super().__init__()
        if isinstance(usr, User):
            self.user = usr

        if repo:

            owner = str_short_user(repo.owner)

            def get_colabs():
                try:
                    collaborators = [str_short_user(x) for x in repo.collaborators()]
                    return collaborators, True
                except ForbiddenError as fe:
                    collaborators = []
                    print(fe)
                    return collaborators, False

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # Submit the tasks to the executor
                future1 = executor.submit(iter_long, repo.commit_activity)
                future2 = executor.submit(iter_long, repo.code_frequency)
                future3 = executor.submit(get_colabs)
                future4 = executor.submit(repo.pull_requests, state='open', sort='updated')

                # Wait for all tasks to complete
                concurrent.futures.wait([future3])
                collaborators, collaborators_access = future3.result()

                commits = {}
                for usr in collaborators + [owner]:
                    commits[usr['login']] = [int(get_gh_datetime(x.commit.committer['date']).timestamp())
                                             for x in repo.commits(author=usr['login'])]
                    sleep(1)

                concurrent.futures.wait([future1, future2, future4])

                # Retrieve results
                commit_activity = future1.result()
                code_frequency = future2.result()
                pull_requests = [str_short_pull_request(x) for x in future4.result()]
                pull_requests_count = len(pull_requests)

            # print('\n'.join(f'{key}: {len(array)}' for key, array in commits.items()))
            self.id = repo.id
            self.cached_at = now()
            self.owner = owner
            self.private = bool(repo.private)
            self.name = repo.name
            self.full_name = repo.full_name
            self.description = str(repo.description)
            self.created_at = get_gh_datetime(repo.created_at)
            self.updated_at = get_gh_datetime(repo.updated_at)
            self.homepage = str(repo.homepage)
            self.language = str(repo.language)
            self.archived = bool(repo.archived)
            self.forks_count = int(repo.forks_count)
            self.open_issues_count = int(repo.open_issues_count)
            self.pull_requests_count = int(pull_requests_count)
            self.pull_requests = pull_requests
            self.watchers_count = int(repo.watchers_count)
            self.url = str(repo.html_url)
            self.collaborators = collaborators
            self.collaborators_access = collaborators_access
            self.commit_activity = commit_activity
            self.commits = commits
            self.code_freq = code_frequency
            self.branches = [x.name for x in repo.branches()]
            self.branch_count = len(self.branches)
        else:
            self.id = _id
            self.cached_at = cached_at
            self.owner = owner
            self.private = private
            self.name = name
            self.full_name = full_name
            self.description = description
            self.created_at = created_at
            self.updated_at = updated_at
            self.homepage = homepage
            self.language = language
            self.archived = archived
            self.forks_count = forks_count
            self.open_issues_count = open_issues_count
            self.pull_requests_count = pull_requests_count
            self.pull_requests = pull_requests
            self.watchers_count = watchers_count
            self.url = url
            self.collaborators = collaborators
            self.collaborators_access = collaborators_access
            self.commit_activity = commit_activity
            self.commits = commits
            self.code_freq = code_freq
            self.branches = branches
            self.branch_count = branch_count

    def dump(self):
        return {
            "id": self.id,
            "cached_at": self.cached_at,
            "owner": self.owner,
            "private": self.private,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "homepage": self.homepage,
            "language": self.language,
            "archived": self.archived,
            "forks_count": self.forks_count,
            "open_issues_count": self.open_issues_count,
            "pull_requests_count": self.pull_requests_count,
            "pull_requests": self.pull_requests,
            "watchers_count": self.watchers_count,
            "url": self.url,
            "collaborators": self.collaborators,
            "collaborators_access": self.collaborators_access,
            "commit_activity": self.commit_activity,
            "commits": self.commits,
            "code_freq": self.code_freq,
            "branches": self.branches,
            "branch_count": self.branch_count,
        }

    def __str__(self):
        return str(self.name)
