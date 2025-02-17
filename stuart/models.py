from __future__ import annotations
from typing import Optional, Any, Type, TypeVar, cast, Callable
import logging
from pathlib import Path
from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, sessionmaker
from sqlalchemy import String, Text, DateTime, event, ForeignKey, Column, Integer, UniqueConstraint, select, create_engine
from sqlalchemy.dialects.sqlite import insert
from treelib import Tree
from enum import Enum
import ast

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
    engine = create_engine("sqlite:///./stuart.db")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

class ProgrammingLanguage(Enum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    JAVA = "Java"
    CSHARP = "C#"
    CPP = "C++"
    RUBY = "Ruby"
    GO = "Go"
    SWIFT = "Swift"
    KOTLIN = "Kotlin"
    PHP = "PHP"

class Project(Base):
    """The software project that is being updated or maintained.
    """
    __tablename__ = 'project'

    name: Mapped[str] = mapped_column(String(100),
        nullable=False, index=True,
        doc="Name of the project")
    description: Mapped[Optional[str]] = mapped_column(Text,
        doc="General description of the project's purpose and goals")
    primary_programming_language: Mapped[ProgrammingLanguage] = mapped_column(String(50),
        nullable=False,
        doc="Primary programming language used in the project")
    architectural_description: Mapped[Optional[str]] = mapped_column(Text,
        doc="Description of the project's architectural design and patterns")
    current_state: Mapped[Optional[str]] = mapped_column(String, doc="Any current condition of the project as it pertains to development.")
    rendered_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime,
        doc="Timestamp when the project was last rendered")

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

    def render_package(self, session: Session, root_path: Optional[str | Path]=None) -> None:
        """
        Render a Python package from the models in the database.

        Args:
            session: SQLAlchemy session containing the models
            root_path: the root directory where the package should be rendered, defaults to current directory
        """
        if not self.primary_programming_language == ProgrammingLanguage.PYTHON:
            raise NotImplementedError("Only Python packages are supported for rendering at this time")
        root = Path(root_path or ".").resolve()
        logger.info("Rendering Python package at %s", root)
        src = root / "src"
        src.mkdir(parents=True, exist_ok=True)

        for model_ in (
            (CNode, lambda x : f"{x.name.upper()} = {x.value}", src / "constants.py",),
            (Typing, lambda x : x.body, src / "typings.py",),
            (File, self._render_functions, src / File.name,),
        ):
            self._render_model(session, *model_)

        # Update rendered_timestamp
        self.rendered_timestamp = datetime.now(UTC)
        session.commit()
        logger.info("Package rendering complete")

    @classmethod
    def _render_functions(cls, file: File) -> str:
        filebody = []

        for imp in file.imports:
            filebody.append(str(imp))

        for func in file.functions:
            filebody.append(func.body)
        return "\n".join(filebody)

    @classmethod
    def _render_model(cls, session: "Session",
                    model: Type[Base],
                    render_formatter: Callable,
                    file:Path) -> int:
        """renders the elements of a given model

        Args:
            session (Session): The SQLAlchemy session
            model (Type[Base]): The model to render
            render_formatter (Callable): The formatting function to render each element
            file (Path): The file to write the rendered elements
        Returns:
            int: Number of characters rendered into the target file
        """
        elements = session.query(model).all()
        if not elements:
            logger.info("No %s to render, skipping", model.__name__)
            return 0

        logger.info("Rendering %d %s", len(elements), model.__name__)
        file_body = []
        for element in elements:
            file_body.append(render_formatter(element))
        file.write_text("\n".join(file_body))

    def extract_changes(self, session: Session, root_path: Optional[str | Path]=None) -> list[str]:
        """
        Extract changes from the rendered package and apply them to the project functions, typings, and constants in the database.

        Args:
            session: SQLAlchemy session containing the models
            root_path: the root directory where the package is rendered, defaults to current directory

        Returns:
            List of informative strings about created or updated elements
        """
        root = Path(root_path or ".").resolve()
        src = root / "src"
        if not src.exists():
            logger.warning("Source directory %s does not exist", src)
            return []

        for file_path in src.glob("**/*.py"):
            if file_path.stat().st_mtime <= self.rendered_timestamp.timestamp():
                continue

            with file_path.open("r") as file:
                tree = ast.parse(file.read(), filename=str(file_path))

            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    created = self._upsert_function(session, file_path, node)
                    yield f"function {file_path.stem}.{node.name} was {'created' if created else 'updated'}"
                elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                    created = self._upsert_constant(session, node)
                    yield f"constant {node.targets[0].id} was {'created' if created else 'updated'}"
                elif isinstance(node, ast.ClassDef) and any(base.id == "BaseModel" for base in node.bases if isinstance(base, ast.Name)):
                    created = self._upsert_typing(session, node)
                    yield f"typing {node.name} was {'created' if created else 'updated'}"

        session.commit()
        logger.info("Changes extracted and applied to the database")

    def _upsert_function(self, session: Session, file_path: Path, node: ast.FunctionDef) -> bool:
        """Upsert a function in the database."""
        file = session.query(File).filter_by(name=str(file_path.relative_to("src"))).first()
        if not file:
            file = File(name=str(file_path.relative_to("src")))
            session.add(file)
            session.flush()

        function, created = FNode.get_or_create(session, file_id=file.id, name=node.name)
        function.body = ast.unparse(node)
        session.add(function)
        return created

    def _upsert_constant(self, session: Session, node: ast.Assign) -> bool:
        """Upsert a constant in the database."""
        name = node.targets[0].id
        value = ast.unparse(node.value)
        constant, created = CNode.get_or_create(session, name=name)
        constant.value = value
        session.add(constant)
        return created

    def _upsert_typing(self, session: Session, node: ast.ClassDef) -> bool:
        """Upsert a typing in the database."""
        name = node.name
        body = ast.unparse(node)
        typing, created = Typing.get_or_create(session, name=name)
        typing.body = body
        session.add(typing)
        return created

class File(Base):
    """A file in the project's codebase.
    """
    __tablename__ = 'file'

    name: Mapped[str] = mapped_column(String(255),
        nullable=False, unique=True, index=True,
        doc="path to the file relative to the project root")
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

