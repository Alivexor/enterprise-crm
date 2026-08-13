import asyncio
from collections.abc import Mapping
from typing import Any, NoReturn

import httpx

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.repositories.organization import OrganizationRepository
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.services.development_seed import DevelopmentSeedService


class AuthenticationVerificationError(Exception):
    """Raised when the development authentication flow does not verify."""


def _fail(message: str) -> NoReturn:
    raise AuthenticationVerificationError(message)


def _seed_development_admin() -> None:
    seed_service = DevelopmentSeedService(
        get_settings(),
        OrganizationRepository(),
        PermissionRepository(),
        RoleRepository(),
        UserRepository(),
    )
    with SessionLocal() as database_session:
        seed_service.seed(database_session)


def _expect_mapping(value: Any, description: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{description} was not a JSON object")
    return value


async def verify_authentication() -> None:
    settings = get_settings()
    _seed_development_admin()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": str(settings.default_admin_email),
                "password": settings.default_admin_password.get_secret_value(),
            },
        )
        if login_response.status_code != 200:
            _fail(f"Login endpoint returned HTTP {login_response.status_code}")

        token_payload = _expect_mapping(login_response.json(), "Login response")
        access_token = token_payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            _fail("Login response did not contain an access token")
        refresh_token = token_payload.get("refresh_token")
        if not isinstance(refresh_token, str) or not refresh_token:
            _fail("Login response did not contain a refresh token")

        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if me_response.status_code != 200:
            _fail(f"Authenticated /auth/me returned HTTP {me_response.status_code}")

        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        if refresh_response.status_code != 200:
            _fail(f"Refresh endpoint returned HTTP {refresh_response.status_code}")
        refreshed_payload = _expect_mapping(refresh_response.json(), "Refresh response")
        refreshed_access_token = refreshed_payload.get("access_token")
        if not isinstance(refreshed_access_token, str) or not refreshed_access_token:
            _fail("Refresh response did not contain an access token")

        refreshed_me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refreshed_access_token}"},
        )
        if refreshed_me_response.status_code != 200:
            _fail(
                "Authenticated /auth/me with a refreshed token returned "
                f"HTTP {refreshed_me_response.status_code}"
            )

    user_payload = _expect_mapping(me_response.json(), "/auth/me response")
    expected_values = {
        "organization_id": str(settings.default_organization_id),
        "email": str(settings.default_admin_email).lower(),
        "first_name": settings.default_admin_first_name.strip(),
        "last_name": settings.default_admin_last_name.strip(),
        "is_active": True,
    }
    for field_name, expected_value in expected_values.items():
        if user_payload.get(field_name) != expected_value:
            _fail(f"/auth/me returned an unexpected {field_name}")

    roles = user_payload.get("roles")
    if not isinstance(roles, list) or "admin" not in {
        role.get("name") for role in roles if isinstance(role, Mapping)
    }:
        _fail("/auth/me did not return the admin role")

    permissions = user_payload.get("permissions")
    if not isinstance(permissions, list) or "companies.read" not in {
        permission.get("name")
        for permission in permissions
        if isinstance(permission, Mapping)
    }:
        _fail("/auth/me did not return the expected admin permissions")


def main() -> None:
    try:
        asyncio.run(verify_authentication())
    except Exception as exc:
        print(f"Authentication verification failed: {exc}")
        raise SystemExit(1) from exc

    print(
        "Authentication verification passed: login, refresh, and authenticated "
        "/auth/me succeeded"
    )


if __name__ == "__main__":
    main()
