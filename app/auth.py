import base64
import json
from typing import List, Optional

from fastapi import Header, HTTPException, Request, status
from pydantic import BaseModel

from app.config import settings


class UserContext(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    roles: List[str]


# Local development users.
# These simulate users who would normally come from Microsoft Entra ID.
DEMO_USERS = {
    "finance": UserContext(
        user_id="demo_finance_001",
        email="finance.analyst@company.com",
        name="Finance Analyst",
        roles=["finance_analyst"]
    ),
    "supply": UserContext(
        user_id="demo_supply_001",
        email="supply.analyst@company.com",
        name="Supply Chain Analyst",
        roles=["supply_chain_analyst"]
    ),
    "admin": UserContext(
        user_id="demo_admin_001",
        email="admin@company.com",
        name="Admin User",
        roles=["admin"]
    ),
    "employee": UserContext(
        user_id="demo_employee_001",
        email="employee@company.com",
        name="General Employee",
        roles=["employee"]
    )
}


def get_local_user(x_demo_user: Optional[str]) -> UserContext:
    """
    Local-only authentication simulation.

    In local development, pass:
    X-Demo-User: finance
    X-Demo-User: supply
    X-Demo-User: admin
    X-Demo-User: employee
    """

    if not x_demo_user:
        x_demo_user = "finance"

    user = DEMO_USERS.get(x_demo_user.lower())

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown demo user: {x_demo_user}"
        )

    return user


def decode_app_service_principal(encoded_principal: str) -> dict:
    """
    Decode the X-MS-CLIENT-PRINCIPAL header from Azure App Service auth.

    The header is Base64-encoded JSON.
    """

    try:
        decoded_bytes = base64.b64decode(encoded_principal)
        decoded_text = decoded_bytes.decode("utf-8")
        return json.loads(decoded_text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid App Service principal header"
        ) from exc


def extract_claims_from_principal(principal: dict) -> dict:
    """
    Convert App Service claims array into a simple dictionary.

    App Service claims usually appear as:
    {
        "typ": "claim_type",
        "val": "claim_value"
    }
    """

    claims = {}

    for claim in principal.get("claims", []):
        claim_type = claim.get("typ")
        claim_value = claim.get("val")

        if not claim_type:
            continue

        if claim_type not in claims:
            claims[claim_type] = []

        claims[claim_type].append(claim_value)

    return claims


def get_first_claim(claims: dict, possible_names: list[str], default: str = "") -> str:
    for name in possible_names:
        values = claims.get(name)
        if values:
            return values[0]

    return default


def get_roles_from_claims(claims: dict) -> list[str]:
    """
    Extract roles from common Microsoft Entra claim names.

    App roles usually appear in the 'roles' claim.
    Groups may appear in group-related claims depending on configuration.
    """

    possible_role_claims = [
        "roles",
        "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
    ]

    roles = []

    for claim_name in possible_role_claims:
        roles.extend(claims.get(claim_name, []))

    # Keep only unique roles.
    return sorted(set(roles))


def get_production_user(
    request: Request,
    x_ms_client_principal: Optional[str]
) -> UserContext:
    """
    Production-style identity extraction.

    This expects Azure App Service authentication to have already authenticated
    the user and injected identity headers.
    """

    if not x_ms_client_principal:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authenticated principal"
        )

    principal = decode_app_service_principal(x_ms_client_principal)
    claims = extract_claims_from_principal(principal)

    email = get_first_claim(
        claims,
        [
            "preferred_username",
            "email",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
        ],
        default="unknown@company.com"
    )

    name = get_first_claim(
        claims,
        [
            "name",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
        ],
        default=email
    )

    user_id = get_first_claim(
        claims,
        [
            "oid",
            "sub",
            "http://schemas.microsoft.com/identity/claims/objectidentifier"
        ],
        default=email
    )

    roles = get_roles_from_claims(claims)

    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user has no assigned application roles"
        )

    return UserContext(
        user_id=user_id,
        email=email,
        name=name,
        roles=roles
    )


async def get_current_user(
    request: Request,
    x_demo_user: Optional[str] = Header(default=None),
    x_ms_client_principal: Optional[str] = Header(default=None)
) -> UserContext:
    """
    FastAPI dependency for retrieving the current user.

    Local mode:
        Uses X-Demo-User.

    Production mode:
        Uses Azure App Service authentication headers.
    """

    if settings.auth_mode == "local":
        return get_local_user(x_demo_user)

    if settings.auth_mode == "production":
        return get_production_user(
            request=request,
            x_ms_client_principal=x_ms_client_principal
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported AUTH_MODE: {settings.auth_mode}"
    )


def require_any_role(user: UserContext, allowed_roles: list[str]) -> None:
    """
    Simple authorization helper.

    Use this when an endpoint itself should only be accessible to certain roles.
    """

    if "admin" in user.roles:
        return

    if not set(user.roles).intersection(set(allowed_roles)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )