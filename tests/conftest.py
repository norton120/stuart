from typing import Type, Generator
import pytest
import factory
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from stuart.models import Project, File, Base

class ProjectFactory(factory.Factory):
    """Factory for creating Project instances in tests."""

    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Test Project {n}")
    description = "Sample Description"
    architectural_description = "Sample Architectural Description"
    current_state = "planning"

class FileFactory(factory.Factory):
    """Factory for creating File instances in tests."""

    class Meta:
        model = File

    filename = factory.Sequence(lambda n: f"test/path/file_{n}.py")
    suffix = ".py"
    description = "A sample Python file"

@pytest.fixture
def project_factory() -> Type[ProjectFactory]:
    return ProjectFactory

@pytest.fixture
def file_factory() -> Type[FileFactory]:
    return FileFactory

@pytest.fixture
def engine() -> Engine:
    """Create an in-memory SQLite database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    """Provide a transactional scope around tests."""
    with Session(engine) as session:
        yield session
        session.rollback()