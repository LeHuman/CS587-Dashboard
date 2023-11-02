"""Github API wrapper using the github3 library"""
from github3 import login
from github3.users import AuthenticatedUser

class Github3APIError(Exception):
    """Generic Github3 API error"""
    def __init__(self):
        super().__init__("Generic Github3 API error")

def get_user(token:str) -> AuthenticatedUser:
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

    return me
