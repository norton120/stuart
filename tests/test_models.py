import pytest
from sqlalchemy.exc import IntegrityError
from stuart.models import Project, File

def test_create_project(session, project_factory):
    # Create project instance
    project = project_factory()

    # Save to database
    session.add(project)
    session.commit()

    # Verify it was saved
    saved_project = session.get(project.__class__, project.id)
    assert saved_project.name == "Test Project 0"  # Changed to match factory output
    assert saved_project.description == "Sample Description"

def test_create_file(session, file_factory):
    # Create file instance
    file = file_factory()

    # Save to database
    session.add(file)
    session.commit()

    # Verify it was saved
    saved_file = session.get(file.__class__, file.id)
    assert saved_file.filename == "test/path/file_0.py"
    assert saved_file.suffix == ".py"
    assert saved_file.description == "A sample Python file"

def test_file_unique_filename(session, file_factory):
    # Create and save first file
    file1 = file_factory(filename="same/path/file.py")
    session.add(file1)
    session.commit()

    # Try to create second file with same filename
    file2 = file_factory(filename="same/path/file.py")
    session.add(file2)

    # Should raise integrity error due to unique constraint
    with pytest.raises(IntegrityError):
        session.commit()
