import pytest
from sqlalchemy.exc import IntegrityError
from stuart.models import Project, File, Typing, CNode, FNode
import tempfile
from pathlib import Path
from stuart.models import render_package

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
    assert saved_fnode.return_type == "bool"  # Verify return type

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

def test_render_package(
    session,
    file_factory,
    fnode_factory,
    file_import_factory,
    typing_factory,
    cnode_factory
):
    """Test complete package rendering with all model types."""
    # Create sample typing
    type_def = typing_factory(
        name="UserType",
        description="Custom user type definition",
        body="type User = { name: string; age: number; }"
    )
    session.add(type_def)

    # Create sample constant
    constant = cnode_factory(
        name="MAX_USERS",
        value="100"
    )
    session.add(constant)

    # Create sample file with imports and functions
    file = file_factory(
        filename="src/users.py",
        description="User management module"
    )
    session.add(file)

    # Add imports to file
    imports = [
        file_import_factory(
            file=file,
            imported="typing",
            from_path=None,
            alias=None
        ),
        file_import_factory(
            file=file,
            imported="User",
            from_path=".types",
            alias=None
        )
    ]
    session.add_all(imports)

    # Add function to file
    function = fnode_factory(
        file=file,
        name="get_user",
        description="Retrieve user by ID",
        body="def get_user(user_id: int) -> User:\n    return {'name': 'test', 'age': 30}",
        return_type="User"
    )
    session.add(function)

    session.commit()

    # Render package to temp directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        render_package(session, tmp_dir)

        # Check directory structure
        root = Path(tmp_dir)
        assert (root / "typings.py").is_file()
        assert (root / "constants.py").is_file()
        assert (root / "src").is_dir()
        assert (root / "src" / "users.py").is_file()

        # Check typings content
        typings_content = (root / "typings.py").read_text()
        assert "type User = { name: string; age: number; }" in typings_content
        assert "Custom user type definition" in typings_content

        # Check constants content
        constants_content = (root / "constants.py").read_text()
        assert "MAX_USERS = 100" in constants_content

        # Check file content
        users_content = (root / "src" / "users.py").read_text()
        assert "import typing" in users_content
        assert "from .types import User" in users_content
        assert "User management module" in users_content
        assert "def get_user(user_id: int) -> User:" in users_content

def test_render_package_empty(session):
    """Test package rendering with no models."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        render_package(session, tmp_dir)
        root = Path(tmp_dir)
        assert root.exists()
        assert not list(root.glob("*.py"))  # No Python files should be created

def test_render_package_nested_directories(session, file_factory):
    """Test package rendering with deeply nested directories."""
    file = file_factory(filename="deep/nested/path/module.py")
    session.add(file)
    session.commit()

    with tempfile.TemporaryDirectory() as tmp_dir:
        render_package(session, tmp_dir)
        root = Path(tmp_dir)
        assert (root / "deep" / "nested" / "path" / "module.py").is_file()
