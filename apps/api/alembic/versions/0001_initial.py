"""Initial game schema with immutable event tables."""

import rivalry.models  # noqa: F401
from alembic import op
from rivalry.db import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind())
    op.execute("""
    CREATE FUNCTION reject_event_change() RETURNS trigger AS $$
    BEGIN RAISE EXCEPTION 'event rows are append-only'; END;
    $$ LANGUAGE plpgsql;
    """)
    for table in ("submissions", "score_revisions", "score_notices", "confirmations", "void_events"):
        op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION reject_event_change()")


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())
    op.execute("DROP FUNCTION reject_event_change()")
