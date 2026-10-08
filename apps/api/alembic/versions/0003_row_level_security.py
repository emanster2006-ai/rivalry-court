"""Enable row level security on every table in the public schema.

Hosted Supabase exposes the public schema over its REST API to anyone holding the
publishable key. With row level security on and no policies, that API sees nothing;
the game API connects as the table owner, which is not subject to the restriction.
It is harmless on plain PostgreSQL.
"""

from alembic import op

revision = "0003_row_level_security"
down_revision = "0002_usernames"
branch_labels = None
depends_on = None

TABLES_SQL = "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"


def upgrade() -> None:
    op.execute(f"""
        DO $$
        DECLARE t text;
        BEGIN
          FOR t IN {TABLES_SQL} LOOP
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
          END LOOP;
        END $$;
    """)


def downgrade() -> None:
    op.execute(f"""
        DO $$
        DECLARE t text;
        BEGIN
          FOR t IN {TABLES_SQL} LOOP
            EXECUTE format('ALTER TABLE public.%I DISABLE ROW LEVEL SECURITY', t);
          END LOOP;
        END $$;
    """)
