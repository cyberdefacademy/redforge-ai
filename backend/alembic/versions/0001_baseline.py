"""Baseline schema for REDFORGE AI v0.7.1.

Creates all tables from SQLAlchemy metadata. Future changes must add new
incremental revisions; never edit this file after first prod deploy.
Revision ID: 0001_baseline
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from app.core.database import Base
    import app.models.user  # noqa: F401
    import app.models.engagement  # noqa: F401
    import app.models.scope  # noqa: F401
    import app.models.asset  # noqa: F401
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    from app.core.database import Base
    import app.models.user  # noqa: F401
    import app.models.engagement  # noqa: F401
    import app.models.scope  # noqa: F401
    import app.models.asset  # noqa: F401
    Base.metadata.drop_all(bind=bind)
