from __future__ import annotations
from typing import Optional, Any, Type, TypeVar, cast
import logging
from pathlib import Path
from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, sessionmaker
from sqlalchemy import String, Text, DateTime, event, ForeignKey, Column, Integer, UniqueConstraint, select, create_engine
from sqlalchemy.dialects.sqlite import insert
from treelib import Tree

logger = logging.getLogger(__name__)

"""Guidelines
- All models (not including join table models) inherit from a base class that has an "id" primary key.
- Models should use Sqlalchemy's 2.0 Mapped and mapped_column syntax for defining columns.
- Models should use singluar table names.
- Columns should always have descriptions.
- Models should have a heredoc explaining what the model represents.

"""

T = TypeVar('T', bound='Base')

class Base(DeclarativeBase):
    """Base class for all models providing common fields."""
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True,
        doc="Unique identifier for all model instances")
    created_at: Mapped[datetime] = mapped_column(DateTime,
        default=lambda: datetime.now(UTC),
        doc="Timestamp when the record was created")
    updated_at: Mapped[datetime] = mapped_column(DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        doc="Timestamp when the record was last updated")

    @classmethod
    def upsert(cls: Type[T], session: Session, **kwargs: Any) -> tuple[T, bool]:
        """
        Get an existing record by name or create a new one.

        Args:
            session: SQLAlchemy session
            **kwargs: Fields to set on the model

        Returns:
            Tuple (instance, created) of the model, either updated or newly created
        """
        # Check for name field which all our models use as primary identifier
        if 'name' not in kwargs:
            logger.warning("No name field provided for %s upsert, falling back to insert", cls.__name__)
            instance = cls(**kwargs)
            session.add(instance)
            return instance, True

        # Try to find existing record by name
        instance = session.execute(select(cls).filter_by(name=kwargs['name'])).scalar_one_or_none()

        if instance:
            logger.info("Updating existing %s: %s", cls.__name__, kwargs['name'])
            for key, value in kwargs.items():
                setattr(instance, key, value)
            created = False
        else:
            logger.info("Creating new %s: %s", cls.__name__, kwargs['name'])
            instance = cls(**kwargs)
            session.add(instance)
            created = True

        return instance, created

    @classmethod
    def get_or_create(cls: Type[T], session: Session, **kwargs: Any) -> tuple[T, bool]:
        """
        Get an existing record by name or create a new one.
        Does not update existing records.

        Args:
            session: SQLAlchemy session
            **kwargs: Fields to set on the model

        Returns:
            Tuple of (instance, created) where created is True if a new record was created
        """
        if 'name' not in kwargs:
            logger.warning("No name field provided for %s get_or_create, falling back to create", cls.__name__)
            instance = cls(**kwargs)
            session.add(instance)
            return instance, True

        instance = session.execute(select(cls).filter_by(name=kwargs['name'])).scalar_one_or_none()

        if instance:
            logger.debug("Found existing %s: %s", cls.__name__, kwargs['name'])
            return instance, False

        logger.info("Creating new %s: %s", cls.__name__, kwargs['name'])
        instance = cls(**kwargs)
        session.add(instance)
        session.flush()
        return instance, True



def get_session() -> Session:
    """Get a database session for stuart."""
    # Add session management
    engine = create_engine("sqlite:///stuart.db")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

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

    def tree(self, session: Session) -> str:
        """
        Generate a tree-style representation of the project structure.
        """
        logger.info("Generating tree for project %s", self.name)
        tree = Tree()
        tree.create_node(f"{self.name}/", "root")

        # Get all files and sort by path
        files = session.query(File).order_by(File.name).all()

        # Track processed paths to handle directories
        processed = {"root"}

        for file in files:
            parts = Path(file.name).parts
            current = "root"

            # Add directory nodes
            for part in parts[:-1]:
                parent = current
                current = f"{current}/{part}"
                if current not in processed:
                    tree.create_node(f"{part}/", current, parent=parent)
                    processed.add(current)

            # Add file node
            file_id = f"{current}/{parts[-1]}"
            tree.create_node(parts[-1], file_id, parent=current)

            # Add function nodes
            for func in file.functions:
                tree.create_node(
                    f"{func.name}()",
                    f"{file_id}/{func.name}",
                    parent=file_id
                )

        return tree.show(stdout=False)

class File(Base):
    """A file in the project's codebase.
    """
    __tablename__ = 'file'

    name: Mapped[str] = mapped_column(String(255),
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
    imported = Column(String, nullable=False)
    from_path = Column(String, nullable=True)
    alias = Column(String, nullable=True)

    file = relationship("File", back_populates="imports")

    # Update unique constraint to use ON CONFLICT DO NOTHING
    __table_args__ = (
        UniqueConstraint('file_id', 'imported', 'from_path', 'alias',
                        name='unique_import',
                        sqlite_on_conflict='IGNORE'),
    )

    def __repr__(self) -> str:
        statement = f"import {self.imported}"
        if self.from_path:
            statement = f"from {self.from_path} {statement}"
        if self.alias:
            statement += f" as {self.alias}"
        return statement

def render_package(session: Session, root_path: str | Path) -> None:
    """
    Render a Python package from the models in the database.

    Args:
        session: SQLAlchemy session containing the models
        root_path: Path to the project root directory
    """
    root = Path(root_path).resolve()
    logger.info("Rendering Python package at %s", root)
    root.mkdir(parents=True, exist_ok=True)

    # Render typings file
    typings = session.query(Typing).all()
    if typings:
        logger.info("Rendering %d type definitions", len(typings))
        typings_file = root / "typings.py"
        typings_file.write_text(
            "\"\"\"Type definitions for the project.\"\"\"\n\n" +
            "".join(
                f"# {typing.description}\n{typing.body}\n\n"
                for typing in typings
            )
        )

    # Render constants file
    constants = session.query(CNode).all()
    if constants:
        logger.info("Rendering %d constants", len(constants))
        constants_file = root / "constants.py"
        constants_file.write_text(
            "\"\"\"Project constants.\"\"\"\n\n" +
            "".join(f"{const.name.upper()} = {const.value}\n" for const in constants)
        )

    # Render individual files with their functions
    for file in session.query(File).all():
        logger.info("Rendering file %s", file.name)
        file_path = root / file.name
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = [
            *[f"{imp}\n" for imp in file.imports],
            "\n" if file.imports else "",
            f"\"\"\"{file.description}\"\"\"\n\n" if file.description else "",
            *[
                f"{f'\"\"\"{func.description}\"\"\"\n' if func.description else ''}"
                f"{func.body}\n\n"
                for func in file.functions
            ]
        ]

        file_path.write_text("".join(content))

    logger.info("Package rendering complete")