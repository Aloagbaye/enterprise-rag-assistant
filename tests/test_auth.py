import pytest
from fastapi import HTTPException

from app.auth import get_local_user, require_any_role


def test_get_finance_user():
    user = get_local_user("finance")

    assert user.email == "finance.analyst@company.com"
    assert "finance_analyst" in user.roles


def test_get_admin_user():
    user = get_local_user("admin")

    assert user.email == "admin@company.com"
    assert "admin" in user.roles


def test_unknown_user_fails():
    with pytest.raises(HTTPException):
        get_local_user("unknown")


def test_admin_can_access_admin_route():
    user = get_local_user("admin")

    require_any_role(user, ["admin"])


def test_finance_user_cannot_access_admin_route():
    user = get_local_user("finance")

    with pytest.raises(HTTPException):
        require_any_role(user, ["admin"])