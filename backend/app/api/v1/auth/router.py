from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.auth import (
    LoginRequest,
    MfaConfirmRequest,
    MfaConfirmResponse,
    MfaDisableRequest,
    MfaSetupResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.security.dependencies import CurrentUser
from app.security.password import verify_password
from app.security.totp import build_otpauth_uri, decrypt_secret, encrypt_secret, generate_recovery_codes, generate_secret, hash_recovery_code, verify_code
from app.core.config import get_settings
from app.services.auth import (
    AuthenticationConfigurationError,
    AuthenticationError,
    AuthenticationMfaInvalidError,
    AuthenticationMfaRequiredError,
    AuthenticationSessionError,
    SelfRegistrationDisabledError,
    UserAlreadyExistsError,
    auth_service,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    registration: RegisterRequest,
    database_session: DatabaseSession,
) -> UserResponse:
    try:
        user = auth_service.create_user(database_session, registration)
    except SelfRegistrationDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is disabled",
        ) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from exc
    except AuthenticationConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication registration is not configured",
        ) from exc
    return auth_service.get_user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    database_session: DatabaseSession,
) -> TokenResponse:
    try:
        return auth_service.authenticate(database_session, credentials)
    except AuthenticationMfaRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA code required",
            headers={"X-CRM-MFA": "required"},
        ) from exc
    except AuthenticationMfaInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code",
            headers={"X-CRM-MFA": "invalid"},
        ) from exc
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except AuthenticationSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from exc


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    token_request: RefreshTokenRequest,
    database_session: DatabaseSession,
) -> TokenResponse:
    try:
        return auth_service.refresh_authentication_tokens(
            database_session, token_request.refresh_token
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except AuthenticationSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token_request: RefreshTokenRequest,
    database_session: DatabaseSession,
) -> None:
    try:
        auth_service.logout(database_session, token_request.refresh_token)
    except AuthenticationSessionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from exc


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser) -> UserResponse:
    return auth_service.get_user_response(current_user)


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def setup_mfa(current_user: CurrentUser, database_session: DatabaseSession) -> MfaSetupResponse:
    settings = get_settings()
    secret = generate_secret()
    current_user.mfa_secret_encrypted = encrypt_secret(secret, settings.jwt_secret.get_secret_value())
    current_user.mfa_enabled = False
    current_user.mfa_recovery_codes = []
    database_session.commit()
    return MfaSetupResponse(
        secret=secret,
        otpauth_uri=build_otpauth_uri(secret, issuer="Enterprise CRM", account_name=current_user.email),
    )


@router.post("/mfa/confirm", response_model=MfaConfirmResponse)
def confirm_mfa(data: MfaConfirmRequest, current_user: CurrentUser, database_session: DatabaseSession) -> MfaConfirmResponse:
    settings = get_settings()
    if not current_user.mfa_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Start MFA setup first")
    secret = decrypt_secret(current_user.mfa_secret_encrypted, settings.jwt_secret.get_secret_value())
    if not verify_code(secret, data.code):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid MFA code")
    recovery_codes = generate_recovery_codes()
    current_user.mfa_enabled = True
    current_user.mfa_recovery_codes = [hash_recovery_code(code, settings.jwt_secret.get_secret_value()) for code in recovery_codes]
    auth_service.revoke_user_refresh_sessions(database_session, organization_id=current_user.organization_id, user_id=current_user.id)
    database_session.commit()
    return MfaConfirmResponse(recovery_codes=recovery_codes)


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
def disable_mfa(data: MfaDisableRequest, current_user: CurrentUser, database_session: DatabaseSession) -> Response:
    valid_password, _ = verify_password(data.password, current_user.password_hash)
    if not valid_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    if current_user.mfa_enabled:
        settings = get_settings()
        if not current_user.mfa_secret_encrypted:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MFA configuration is incomplete")
        secret = decrypt_secret(current_user.mfa_secret_encrypted, settings.jwt_secret.get_secret_value())
        recovery_digest = hash_recovery_code(data.code, settings.jwt_secret.get_secret_value())
        recovery_hashes = list(current_user.mfa_recovery_codes or [])
        valid_second_factor = verify_code(secret, data.code) or recovery_digest in recovery_hashes
        if not valid_second_factor:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid MFA code")
    current_user.mfa_enabled = False
    current_user.mfa_secret_encrypted = None
    current_user.mfa_recovery_codes = None
    auth_service.revoke_user_refresh_sessions(database_session, organization_id=current_user.organization_id, user_id=current_user.id)
    database_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
