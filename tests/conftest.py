import pytest
import factory
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from stewart.models import Project, Base

class ProjectFactory(factory.Factory):
    class Meta:
        model = Project

    name = "Sample Project"
    description = "Sample Description"
    architectural_description = "Sample Architectural Description"
    current_state = "Sample Current State"

@pytest.fixture
def project_factory():
    return ProjectFactory

@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session
        session.rollback()