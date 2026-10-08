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


def _ec_keys():
    from cryptography.hazmat.primitives.asymmetric import ec

    return ec.generate_private_key(ec.SECP256R1()), ec.generate_private_key(ec.SECP256R1())


class _FakeJwks:
    def __init__(self, public_key) -> None:
        self.public_key = public_key

    def get_signing_key_from_jwt(self, _token):
        return type("Key", (), {"key": self.public_key})()


def test_public_key_tokens_are_verified_when_a_jwks_url_is_set(monkeypatch) -> None:
    import pytest

    from rivalry import auth

    trusted, attacker = _ec_keys()
    monkeypatch.setattr(settings, "auth_jwks_url", "https://example.supabase.co/auth/v1/.well-known/jwks.json")
    monkeypatch.setattr(auth, "jwks_client", lambda _url: _FakeJwks(trusted.public_key()))
    claims = {"sub": str(uuid.uuid4()), "email": "a@example.com", "aud": "authenticated"}

    good = jwt.encode(claims, trusted, algorithm="ES256")
    assert auth.decode_token(good)["email"] == "a@example.com"

    forged = jwt.encode(claims, attacker, algorithm="ES256")
    with pytest.raises(jwt.InvalidSignatureError):
        auth.decode_token(forged)

    # The shared secret must not be accepted once public-key mode is on.
    shared = jwt.encode(claims, settings.auth_jwt_secret, algorithm="HS256")
    with pytest.raises(jwt.InvalidAlgorithmError):
        auth.decode_token(shared)

    wrong_audience = jwt.encode({**claims, "aud": "other"}, trusted, algorithm="ES256")
    with pytest.raises(jwt.InvalidAudienceError):
        auth.decode_token(wrong_audience)
