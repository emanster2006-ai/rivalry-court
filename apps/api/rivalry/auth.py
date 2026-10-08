import uuid
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rivalry.config import settings
from rivalry.db import get_db
from rivalry.models import User

bearer = HTTPBearer()


@lru_cache
def jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_keys=True, lifespan=600)


def decode_token(token: str) -> dict:
    """Verify a sign-in token: public-key (JWKS) when configured, else the shared secret."""
    if settings.auth_jwks_url:
        key = jwks_client(settings.auth_jwks_url).get_signing_key_from_jwt(token).key
        return jwt.decode(token, key, algorithms=["ES256", "RS256"], audience="authenticated")
    return jwt.decode(token, settings.auth_jwt_secret, algorithms=["HS256"], audience="authenticated")


def current_user(
    token: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)
) -> User:
    try:
        claims = decode_token(token.credentials)
        user_id = uuid.UUID(claims["sub"])
        email = claims["email"].lower()
    except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        raise HTTPException(401, "Invalid authentication token") from exc
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, email=email)
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            # The first page load requests /me and /groups together. Another
            # request may have inserted this user after our initial lookup.
            db.rollback()
            user = db.get(User, user_id)
            if user is None:
                raise
        else:
            db.refresh(user)
    elif user.email != email:
        user.email = email
        db.commit()
    return user


def membership(db: Session, group_id: uuid.UUID, user_id: uuid.UUID, admin: bool = False):
    from rivalry.models import Membership

    row = db.scalar(
        select(Membership).where(Membership.group_id == group_id, Membership.user_id == user_id)
    )
    if row is None:
        raise HTTPException(404, "Group not found")
    if admin and row.role != "admin":
        raise HTTPException(403, "Group admin required")
    return row
