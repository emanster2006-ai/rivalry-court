import uuid

import jwt
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from rivalry.auth import current_user
from rivalry.config import settings
from rivalry.db import Base
from rivalry.models import User


def test_first_sign_in_recovers_when_another_request_created_the_user(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'auth.db'}")
    Base.metadata.create_all(engine)
    user_id = uuid.uuid4()
    email = "new-member@example.com"
    with Session(engine) as db:
        db.add(User(id=user_id, email=email))
        db.commit()
        real_get = db.get
        first_lookup = True

        def stale_first_lookup(model, key):
            nonlocal first_lookup
            if model is User and key == user_id and first_lookup:
                first_lookup = False
                return None
            return real_get(model, key)

        db.get = stale_first_lookup
        token = jwt.encode(
            {"sub": str(user_id), "email": email, "aud": "authenticated"},
            settings.auth_jwt_secret,
            algorithm="HS256",
        )
        result = current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), db)
        assert result.id == user_id
        assert db.query(User).count() == 1
