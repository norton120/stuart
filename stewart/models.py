from __future__ import annotations
from typing import Optional
import logging
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, event

logger = logging.getLogger(__name__)

"""Guidelines
- All models (not including join table models) inherit from a base class that has an "id" primary key.
- Models should use Sqlalchemy's 2.0 Mapped and mapped_column syntax for defining columns.
- Models should use singluar table names.
- Columns should always have descriptions.
- Models should have a heredoc explaining what the model represents.

"""

class Base(DeclarativeBase):
    """Base class for all models providing common fields."""

    id: Mapped[int] = mapped_column(primary_key=True,
        doc="Unique identifier for all model instances")
    created_at: Mapped[datetime] = mapped_column(DateTime,
        default=datetime.utcnow,
        doc="Timestamp when the record was created")
    updated_at: Mapped[datetime] = mapped_column(DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Timestamp when the record was last updated")

class Project(Base):
    """The software project that is being updated or maintained.
    """
    __tablename__ = 'project'

    name: Mapped[str] = mapped_column(String(100),
        nullable=False, index=True,
        doc="Name of the project")
    description: Mapped[Optional[str]] = mapped_column(Text,
        doc="General description of the project's purpose and goals")
    architectural_description: Mapped[Optional[str]] = mapped_column(Text,
        doc="Description of the project's architectural design and patterns")
    current_state: Mapped[Optional[str]] = mapped_column(String, doc="Any current condition of the project as it pertains to development.")