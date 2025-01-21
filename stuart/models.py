from __future__ import annotations
from typing import Optional
import logging
from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, event, ForeignKey, Column, Integer

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
    functions: Mapped[list["FNode"]] = relationship("FNode", back_populates="file",
        cascade="all, delete-orphan")
    imports: Mapped[list["FileImport"]] = relationship("FileImport", back_populates="file", cascade="all, delete-orphan")

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

class CNode(Base):
    """Configuration node for storing constants.
    """
    __tablename__ = 'c_node'

    name: Mapped[str] = mapped_column(String(255),
        nullable=False, unique=True, index=True,
        doc="Unique variable name for this constant")
    value: Mapped[str] = mapped_column(Text,
        nullable=False,
        doc="Value for this constant")

class FNode(Base):
    """Function defined within a module.
    """
    __tablename__ = 'f_node'

    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"),
        nullable=False, index=True,
        doc="Reference to the file containing this function")
    name: Mapped[str] = mapped_column(String(255),
        nullable=False,
        doc="Name of the function")
    description: Mapped[Optional[str]] = mapped_column(Text,
        doc="Description of what the function does")
    body: Mapped[str] = mapped_column(Text,
        nullable=False,
        doc="The actual function implementation code")
    return_type: Mapped[str] = mapped_column(String(100),
        nullable=False,
        doc="The return type of the function")

    # Relationship to parent file
    file: Mapped["File"] = relationship("File", back_populates="functions")

class FileImport(Base):
    """Model representing import statements in a file."""
    __tablename__ = "file_imports"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("file.id"), nullable=False)
    import_path = Column(String, nullable=False)
    from_path = Column(String, nullable=True)
    alias = Column(String, nullable=True)

    file = relationship("File", back_populates="imports")

    def __repr__(self) -> str:
        if self.from_path:
            if self.alias:
                return f"from {self.from_path} import {self.import_path} as {self.alias}"
            return f"from {self.from_path} import {self.import_path}"
        if self.alias:
            return f"import {self.import_path} as {self.alias}"
        return f"import {self.import_path}"