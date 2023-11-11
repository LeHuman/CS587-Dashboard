"""Github API wrapper using the github3 library"""
from ast import List
from datetime import datetime
from typing import Any, Tuple

from github3 import GitHub, login
from github3.users import AuthenticatedUser
from github3.users import ShortUser
from github3.events import Event
from github3.repos import ShortRepository, Repository
from github3.repos.commit import ShortCommit


def get_datetime_str(dt: datetime | str | None) -> dict[str, str]:
    """Returns a datetime as a string dictionary with human readable or epoch strings

    Args:
        dt (datetime | str | None): The datetime or github formatted time

    Returns:
        dict[str, str]: dictionary with human readable or epoch strings
    """
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            dt = None

    if isinstance(dt, datetime):
        epoch = str(dt.timestamp())
        day = str(dt.strftime("%B %d, %Y"))
        time = str(dt.strftime("%I:%M%p"))
        return {'day': day, 'time': time, 'epoch': epoch}

    return {'human': "None", 'epoch': "0.0"}


class Github3APIError(Exception):
    """Generic Github3 API error"""

    def __init__(self):
        super().__init__("Generic Github3 API error")


def get_user(token: str) -> Tuple[GitHub, AuthenticatedUser]:
    """Get a user instance from the API

    Args:
        token (str): OAuth token to use

    Raises:
        Github3Error: Failed to login or resolve user

    Returns:
        AuthenticatedUser: Instance of API User
    """
    gh = login(token=token)

    if gh is None:
        raise Github3APIError

    me = gh.me()

    if me is None:
        raise Github3APIError

    return gh, me


def str_short_user(usr: ShortUser) -> dict[str, str]:
    """Returns a github3 ShortUser as a string dictionary

    Args:
        usr (ShortUser): The given ShortUser

    Returns:
        dict[str, str]: ShortUser as a string dictionary
    """
    return {
        "id": str(usr.id),
        "login": str(usr.login),
        "avatar_url": str(usr.avatar_url),
        "url": str(usr.html_url),
    }


def str_short_commit(usr: ShortCommit) -> dict[str, str]:
    """Returns a github3 ShortCommit as a string dictionary

    Args:
        usr (ShortCommit): The given ShortCommit

    Returns:
        dict[str, str]: ShortCommit as a string dictionary
    """
    return {
        "id": str(usr.id),
        "login": str(usr.login),
        "avatar_url": str(usr.avatar_url),
        "url": str(usr.html_url),
    }


def str_event(event: Event) -> dict[str, str | dict[str, str]]:
    """Returns a github3 Event as a string dictionary

    Args:
        event (Event): The given Event

    Returns:
        dict[str, str | dict[str, str]]: Event as a string dictionary
    """
    return {
        "actor": event.actor.id,
        "created_at": get_datetime_str(event.created_at),
        "id": event.id,
        "org": event.org.id if event.org else "None",
        "type": event.type,
        "payload": event.payload,
        "repo": event.repo,
        "public": event.public,
    }


def str_short_repository(repo: ShortRepository) -> dict[str, str | dict[str, str]]:
    """Returns a github3 ShortRepository as a string dictionary

    Args:
        repo (ShortRepository): The given ShortRepository

    Returns:
        dict[str, str | dict[str, str]]: ShortRepository as a string dictionary
    """
    return {
        "id": repo.id,
        "name": repo.name,
        "owner": str_short_user(repo.owner),
        "full_name": repo.full_name,
        "description": repo.description,
        "created_at": get_datetime_str(repo.created_at),
        "updated_at": get_datetime_str(repo.updated_at),
        "homepage": repo.homepage,
        "language": repo.language,
        "archived": repo.archived,
        "forks_count": repo.forks_count,
        "open_issues_count": repo.open_issues_count,
        "watchers_count": repo.watchers_count,
        "url": repo.html_url,
    }


def get_repository(access_token: str, repo_id: str | int) -> Repository | None:
    gh, _ = get_user(token=access_token)
    repo = gh.repository_with_id(int(repo_id))

    if not repo:
        print(f"Failed to get repo {repo_id}")
        return

    return repo


def request_profile(access_token: str) -> Tuple[GitHub, AuthenticatedUser, dict[str, Any]]:
    """Immediately returns relevant information about a user's profile, given their access token

    Args:
        access_token (str): A user's access token

    Returns:
        Tuple[GitHub, AuthenticatedUser, dict[str, Any]]: The GitHub instance, current user, and a string dictionary of various attributes
    """
    # TODO: Parallel requests
    gh, gh_usr = get_user(token=access_token)
    repos = [str_short_repository(x) for x in gh.repositories('all', 'created', 'desc')]
    priv_repo_count = len(repos) - gh_usr.public_repos_count
    return gh, gh_usr, {
        "id": gh_usr.id,
        "name": gh_usr.name,
        "login": gh_usr.login,
        "avatar_url": gh_usr.avatar_url,
        "url": gh_usr.html_url,
        "email": gh_usr.email,
        "followers": [str_short_user(x) for x in gh_usr.followers(10)],
        "following": [str_short_user(x) for x in gh_usr.following(10)],
        "bio": gh_usr.bio,
        "company": gh_usr.company,
        "events": [str_event(x) for x in gh_usr.events(True, 10)],
        "starred_repos": [str_short_repository(x) for x in gh_usr.starred_repositories(sort='updated', number=10)],
        "subscriptions": [str_short_repository(x) for x in gh_usr.subscriptions(number=10)],
        "plan": gh_usr.plan,
        "repos": repos,
        "follower_count": gh_usr.followers_count,
        "repo_pub_count": gh_usr.public_repos_count,
        "repo_priv_count": priv_repo_count,
        "gist_pub_count": gh_usr.public_gists_count,
        "repo_first": get_datetime_str(gh.repositories('all', 'created', 'asc', 1).next().created_at),
        "repo_last": get_datetime_str(gh.repositories('all', 'created', 'desc', 1).next().created_at),
        "api_limit": gh_usr.ratelimit_remaining,
    }


def test():
    """API test function"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    current_token = str(os.getenv("CURRENT_TOKEN"))

    gh, gh_usr, profile = request_profile(current_token)

    print(gh)
    print(gh_usr)
    print(profile)
    print(gh_usr.ratelimit_remaining)


if __name__ == "__main__":
    test()
