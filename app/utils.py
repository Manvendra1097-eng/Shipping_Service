from datetime import datetime, timedelta, timezone

import jwt
from uuid import uuid4

from app.database.config import config


def get_token(data: dict, exp: timedelta = timedelta(days=1)):

    return jwt.encode(
        payload={**data, "jti": str(uuid4()), "exp": datetime.now(timezone.utc) + exp},
        key=config.JWT_TOKEN,
        algorithm=config.JWT_ALGO,
    )


def get_payload(token: str) -> dict | None:
    try:
        return jwt.decode(jwt=token, key=config.JWT_TOKEN, algorithms=[config.JWT_ALGO])
    except jwt.PyJWTError:
        return None
