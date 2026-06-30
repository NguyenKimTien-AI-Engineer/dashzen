from core.schemas.auth import UsageSummary, UserResponse
from db.models.user import User
from db.services.avatar_service import build_avatar_url
from db.services.google_oauth_service import build_auth_providers
from db.services.usage_service import get_user_usage
from sqlalchemy.ext.asyncio import AsyncSession


async def build_user_response(session: AsyncSession, user: User) -> UserResponse:
    providers = await build_auth_providers(session, user)
    usage = await get_user_usage(session, user.id)
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=build_avatar_url(user),
        email_verified=user.email_verified,
        has_password=user.password_hash is not None,
        auth_providers=providers,  # type: ignore[arg-type]
        created_at=user.created_at,
        usage=UsageSummary(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        ),
    )
