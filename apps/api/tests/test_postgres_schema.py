import os

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Requires a migrated PostgreSQL test database")
def test_immutable_tables_and_probability_constraint() -> None:
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    with engine.connect() as connection:
        triggers = set(connection.execute(text("""
            SELECT tgname FROM pg_trigger WHERE NOT tgisinternal
        """)).scalars())
        constraints = set(connection.execute(text("""
            SELECT conname FROM pg_constraint WHERE connamespace = 'public'::regnamespace
        """)).scalars())
    assert {f"immutable_{table}" for table in (
        "submissions", "score_revisions", "score_notices", "confirmations", "void_events"
    )} <= triggers
    assert {"probability_step", "nonnegative_scores", "different_members", "claim_type"} <= constraints


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Requires a migrated PostgreSQL test database")
def test_every_public_table_has_row_level_security() -> None:
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    with engine.connect() as connection:
        unprotected = connection.execute(text("""
            SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity
        """)).scalars().all()
    assert unprotected == []
