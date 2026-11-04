# Import every model here so Base.metadata is complete for Alembic autogenerate.
from app.models.user import User

__all__ = ["User"]
