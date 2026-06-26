from core.auth.cookies import clear_auth_cookies, set_auth_cookies
from core.config import get_settings
from core.exceptions import TokenInvalidError
from core.schemas.auth import (
    AuthUserResponse,
    ChangePasswordRequest,
    DeleteAccountRequest,
    LoginRequest,
    OkResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    UpdateProfileRequest,
    UserResponse,
    VerifyEmailRequest,
)
from core.storage.avatar_store import ALLOWED_AVATAR_MIME
from db.models.user import User
from db.services.auth import AuthService
from db.services.avatar_service import AvatarService, build_avatar_url
from db.services.email_verification import EmailVerificationService
from db.session import get_db
from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.rate_limit import rate_limit

router = APIRouter(prefix="/v1/auth", tags=["auth"])
_settings = get_settings()


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=build_avatar_url(user),
        email_verified=user.email_verified,
        created_at=user.created_at,
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(_settings.auth_register_rate_limit)
async def register(
    request: Request,
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    auth_service = AuthService(session)
    user = await auth_service.register(body.email, body.password, body.display_name)
    verification_service = EmailVerificationService(session)
    await verification_service.send_verification_code(user)
    await session.refresh(user)
    return RegisterResponse(user=_user_response(user), requires_verification=True)


@router.post("/verify-email", response_model=OkResponse)
@rate_limit(_settings.auth_verify_rate_limit)
async def verify_email(
    request: Request,
    body: VerifyEmailRequest,
    session: AsyncSession = Depends(get_db),
) -> OkResponse:
    service = EmailVerificationService(session)
    await service.verify_email(body.email, body.code)
    return OkResponse()


@router.post("/resend-verification", response_model=OkResponse)
@rate_limit(_settings.auth_resend_rate_limit)
async def resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    session: AsyncSession = Depends(get_db),
) -> OkResponse:
    service = EmailVerificationService(session)
    await service.resend_verification(body.email)
    return OkResponse()


@router.post("/login", response_model=AuthUserResponse)
@rate_limit(_settings.auth_login_rate_limit)
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> AuthUserResponse:
    service = AuthService(session)
    user = await service.login(body.email, body.password)
    tokens = await service.issue_tokens(user)
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return AuthUserResponse(user=_user_response(user))


@router.post("/refresh", response_model=OkResponse)
@rate_limit(_settings.auth_refresh_rate_limit)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> OkResponse:
    refresh_token = request.cookies.get(get_settings().refresh_cookie_name)
    if not refresh_token:
        raise TokenInvalidError()

    service = AuthService(session)
    _user, tokens = await service.refresh(refresh_token)
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return OkResponse()


@router.post("/logout", response_model=OkResponse)
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> OkResponse:
    refresh_token = request.cookies.get(get_settings().refresh_cookie_name)
    service = AuthService(session)
    await service.logout(refresh_token)
    clear_auth_cookies(response)
    return OkResponse()


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = AuthService(session)
    user = await service.update_profile(current_user, body.display_name)
    return _user_response(user)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AVATAR_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type: {content_type}",
        )

    data = await file.read()
    service = AvatarService(session)
    try:
        user = await service.upload(current_user, data, content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _user_response(user)


@router.delete("/me/avatar", response_model=UserResponse)
async def delete_my_avatar(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = AvatarService(session)
    user = await service.remove(current_user)
    return _user_response(user)


@router.post("/change-password", response_model=OkResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OkResponse:
    service = AuthService(session)
    await service.change_password(
        current_user, body.current_password, body.new_password
    )
    return OkResponse()


@router.delete("/me", response_model=OkResponse)
async def delete_me(
    body: DeleteAccountRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OkResponse:
    refresh_token = request.cookies.get(get_settings().refresh_cookie_name)
    service = AuthService(session)
    if refresh_token:
        await service.logout(refresh_token)
    await service.delete_account(current_user, body.password)
    clear_auth_cookies(response)
    return OkResponse()
