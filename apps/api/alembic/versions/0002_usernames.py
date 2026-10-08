"""Add optional unique usernames for public display."""

from alembic import op

revision = "0002_usernames"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0001 creates metadata from the current models; IF NOT EXISTS also supports
    # a fresh database that receives both migrations in one run.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(24)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_username")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS username")
