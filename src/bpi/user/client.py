from __future__ import annotations

from bpi._generated.user_client import UserReadMethods

from .actions import UserActionMethods


class UserClient(UserReadMethods, UserActionMethods):
    """User/profile and relation API entry point."""
