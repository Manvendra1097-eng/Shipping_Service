from datetime import datetime, timezone

from passlib.context import CryptContext

from app.database.redis import add_jti_to_blacklist
from app.utils import get_token

ctx = CryptContext(schemes=["bcrypt"])


def hash_password(password: str) -> str:
    return ctx.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return ctx.verify(password, hashed_password)


def issue_access_token(name: str, user_id: str, role: str) -> str:
    return get_token(data={"name": name, "id": user_id, "role": role})


async def blacklist_token_if_valid(jti: str, exp: int | float) -> None:
    ex = int(exp) - int(datetime.now(timezone.utc).timestamp())
    if ex <= 0:
        return
    await add_jti_to_blacklist(jti, ex)
