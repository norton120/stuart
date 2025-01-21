from __future__ import annotations
from typing import Optional
import logging
from datetime import datetime, UTC
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
        default=lambda: datetime.now(UTC),
        doc="Timestamp when the record was created")
    updated_at: Mapped[datetime] = mapped_column(DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
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

class File(Base):
    """A file in the project's codebase.
    """
    __tablename__ = 'file'

    filename: Mapped[str] = mapped_column(String(255),
        nullable=False, unique=True, index=True,
        doc="Full path of the file relative to project root")
    suffix: Mapped[str] = mapped_column(String(32),
        nullable=False, index=True,
        doc="File extension (e.g. '.py', '.js', '.md')")
    description: Mapped[Optional[str]] = mapped_column(Text,
        doc="Description of the file's purpose and contents")

class Typing(Base):
    """A type definition that can be used across the project.
    """
    __tablename__ = 'typing'

    name: Mapped[str] = mapped_column(String(100),
        nullable=False, unique=True, index=True,
        doc="Name of the type definition")
    description: Mapped[Optional[str]] = mapped_column(Text,
        doc="Description of what this type represents and how it should be used")
    body: Mapped[str] = mapped_column(Text,
        nullable=False,
        doc="The actual type definition code")