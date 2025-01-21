import pytest
from sqlalchemy.exc import IntegrityError
from stuart.models import Project, File, Typing, CNode, FNode

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

def test_create_typing(session, typing_factory):
    # Create typing instance
    typing = typing_factory()

    # Save to database
    session.add(typing)
    session.commit()

    # Verify it was saved
    saved_typing = session.get(typing.__class__, typing.id)
    assert saved_typing.name == "CustomType0"
    assert saved_typing.description == "A custom type definition"
    assert saved_typing.body == "type CustomType = string | number;"

def test_typing_unique_name(session, typing_factory):
    # Create and save first typing
    typing1 = typing_factory(name="DuplicateType")
    session.add(typing1)
    session.commit()

    # Try to create second typing with same name
    typing2 = typing_factory(name="DuplicateType")
    session.add(typing2)

    # Should raise integrity error due to unique constraint
    with pytest.raises(IntegrityError):
        session.commit()

def test_create_cnode(session, cnode_factory):
    # Create cnode instance
    cnode = cnode_factory()

    # Save to database
    session.add(cnode)
    session.commit()

    # Verify it was saved
    saved_cnode = session.get(cnode.__class__, cnode.id)
    assert saved_cnode.name == "config.key.0"
    assert saved_cnode.value == "value_0"

def test_cnode_unique_name(session, cnode_factory):
    # Create and save first cnode
    cnode1 = cnode_factory(name="unique.key")
    session.add(cnode1)
    session.commit()

    # Try to create second cnode with same name
    cnode2 = cnode_factory(name="unique.key")
    session.add(cnode2)

    # Should raise integrity error due to unique constraint
    with pytest.raises(IntegrityError):
        session.commit()

def test_create_fnode(session, file_factory, fnode_factory):
    # Create file first
    file = file_factory(filename="test/path/specific_file.py")

    # Create fnode instance with specific file
    fnode = fnode_factory(file=file)

    # Save to database
    session.add(file)
    session.add(fnode)
    session.commit()

    # Verify it was saved
    saved_fnode = session.get(fnode.__class__, fnode.id)
    assert saved_fnode.name == "function_0"
    assert saved_fnode.description == "A sample function"
    assert saved_fnode.body == "def sample_function():\n    return True"
    assert saved_fnode.file.filename == "test/path/specific_file.py"

def test_file_functions_relationship(session, file_factory, fnode_factory):
    # Create file with two functions
    file = file_factory()
    fnode1 = fnode_factory(file=file, name="func1")
    fnode2 = fnode_factory(file=file, name="func2")

    session.add(file)
    session.add_all([fnode1, fnode2])
    session.commit()

    # Verify relationship
    saved_file = session.get(File, file.id)
    assert len(saved_file.functions) == 2
    assert {f.name for f in saved_file.functions} == {"func1", "func2"}
