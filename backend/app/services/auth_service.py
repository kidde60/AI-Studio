from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id):
    return await db.get(User, user_id)


async def register_user(db: AsyncSession, request: RegisterRequest) -> User:
    user = User(
        email=request.email.lower(),
        full_name=request.full_name,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
