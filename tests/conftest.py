from typing import Type, Generator
import pytest
import factory
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from stuart.models import Project, File, Typing, CNode, FNode, Base

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

class TypingFactory(factory.Factory):
    """Factory for creating Typing instances in tests."""

    class Meta:
        model = Typing

    name = factory.Sequence(lambda n: f"CustomType{n}")
    description = "A custom type definition"
    body = "type CustomType = string | number;"

class CNodeFactory(factory.Factory):
    """Factory for creating CNode instances in tests."""

    class Meta:
        model = CNode

    name = factory.Sequence(lambda n: f"config.key.{n}")
    value = factory.Sequence(lambda n: f"value_{n}")

class FNodeFactory(factory.Factory):
    """Factory for creating FNode instances in tests."""

    class Meta:
        model = FNode

    file = factory.SubFactory(FileFactory)
    name = factory.Sequence(lambda n: f"function_{n}")
    description = "A sample function"
    body = "def sample_function():\n    return True"
    return_type = "bool"

@pytest.fixture
def project_factory() -> Type[ProjectFactory]:
    return ProjectFactory

@pytest.fixture
def file_factory() -> Type[FileFactory]:
    return FileFactory

@pytest.fixture
def typing_factory() -> Type[TypingFactory]:
    return TypingFactory

@pytest.fixture
def cnode_factory() -> Type[CNodeFactory]:
    return CNodeFactory

@pytest.fixture
def fnode_factory() -> Type[FNodeFactory]:
    return FNodeFactory

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