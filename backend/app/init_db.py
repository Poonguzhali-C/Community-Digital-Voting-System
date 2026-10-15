from .database import Base, engine
from . import models  # noqa: F401


def init_db():
    """Test helper only. Real schema management is done by Alembic."""
    Base.metadata.create_all(bind=engine)
