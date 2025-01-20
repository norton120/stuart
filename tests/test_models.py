
import pytest
from stewart.models import Project

def test_create_project(session, project_factory):
    # Create project instance
    project = project_factory()

    # Save to database
    session.add(project)
    session.commit()

    # Verify it was saved
    saved_project = session.get(project.__class__, project.id)
    assert saved_project.name == "Sample Project"
    assert saved_project.description == "Sample Description"