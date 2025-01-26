from stuart.typing import FileImportModel

def test_file_import_model_from_string():
    """Test the FileImportModel.from_string method with various import statements."""
    # Test simple import
    imports = FileImportModel.from_string("import os")
    assert len(imports) == 1
    assert imports[0].imported == "os"
    assert imports[0].from_path is None
    assert imports[0].alias is None

    # Test import with alias
    imports = FileImportModel.from_string("import os as operating_system")
    assert len(imports) == 1
    assert imports[0].imported == "os"
    assert imports[0].from_path is None
    assert imports[0].alias == "operating_system"

    # Test from import
    imports = FileImportModel.from_string("from os import path")
    assert len(imports) == 1
    assert imports[0].imported == "path"
    assert imports[0].from_path == "os"
    assert imports[0].alias is None

    # Test multiple imports
    imports = FileImportModel.from_string("from os import path, getcwd")
    assert len(imports) == 2
    assert imports[0].imported == "path"
    assert imports[0].from_path == "os"
    assert imports[1].imported == "getcwd"
    assert imports[1].from_path == "os"

    # Test from imports with aliases
    imports = FileImportModel.from_string("from os import path as p, getcwd as gc")
    assert len(imports) == 2
    assert imports[0].imported == "path"
    assert imports[0].from_path == "os"
    assert imports[0].alias == "p"
    assert imports[1].imported == "getcwd"
    assert imports[1].from_path == "os"
    assert imports[1].alias == "gc"
