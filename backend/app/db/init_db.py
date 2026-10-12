"""Create tables that do not exist yet: `python -m app.db.init_db` (run from backend/).

Stopgap until Alembic is introduced. `create_all` never alters an existing table,
so any later column change needs a real migration.
"""

from app.db import models  # noqa: F401  (registers tables on Base.metadata)
from app.db.base import Base
from app.db.session import get_engine

if __name__ == "__main__":
    Base.metadata.create_all(get_engine())
    print("Schema is up to date (missing tables created).")
