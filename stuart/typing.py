from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from logging import getLogger

logger = getLogger(__name__)


class PypiPackage(BaseModel):
    """Package information from PyPI."""
    name: str = Field(description="Name of the Python package")
    version: str = Field(description="Version string of the package")
    description: str = Field(description="Brief description or summary of the package")

class FileImportModel(BaseModel):
    """Import statement in a file."""
    imported: str = Field(description="The module or object being imported")
    from_path: Optional[str] = Field(None, description="Optional source path for the import")
    alias: Optional[str] = Field(None, description="Optional alias for the imported object")

    @classmethod
    def from_string(cls, import_string: str) -> List["FileImportModel"]:
        """takes any valid import statement and returns a list of FileImportModel instances"""
        if "import" not in import_string:
            logger.warning("Invalid import statement: %s", import_string)
            raise ValueError("Invalid import statement")

        parts = import_string.split("import")
        from_path = None
        if "from" in parts[0]:
            from_path = parts[0].replace("from", "").strip()

        imports = parts[1].strip().split(",")
        result = []
        for imp in imports:
            imp = imp.strip()
            if " as " in imp:
                imported, alias = imp.split(" as ")
                result.append(cls(imported=imported.strip(), from_path=from_path, alias=alias.strip()))
            else:
                result.append(cls(imported=imp.strip(), from_path=from_path, alias=None))
        return result

class FunctionModel(BaseModel):
    """Function definition within a module."""
    name: str = Field(description="Name of the function")
    description: Optional[str] = Field(None, description="Docstring or description of the function's purpose")
    body: str = Field(description="Function implementation code")
    return_type: str = Field(description="Return type annotation of the function")

class FileModel(BaseModel):
    """A file in the project's codebase."""
    filename: str = Field(description="Full path of the file relative to project root")
    suffix: str = Field(description="File extension (e.g. '.py', '.js', '.md')")
    description: Optional[str] = Field(None, description="Description of the file's purpose and contents")
    functions: List[FunctionModel] = Field(default_factory=list, description="Functions defined in this file")
    imports: List[FileImportModel] = Field(default_factory=list, description="Import statements in this file")

class TypeDefinition(BaseModel):
    """A type definition that can be used across the project."""
    name: str = Field(description="Name of the type definition")
    description: Optional[str] = Field(None, description="Description of what this type represents")
    body: str = Field(description="The actual type definition code")

class ConstantModel(BaseModel):
    """Configuration node for storing constants."""
    name: str = Field(description="Name of the constant (uppercase)")
    value: str = Field(description="Value of the constant")

class ProjectModel(BaseModel):
    """The software project being updated or maintained."""
    name: str = Field(description="Name of the project")
    description: Optional[str] = Field(None, description="General description of the project's purpose")
    architectural_description: Optional[str] = Field(None, description="Description of the project's architecture")
    current_state: Optional[str] = Field(None, description="Current development state")
    created_at: datetime = Field(description="Timestamp when the project was created")
    updated_at: datetime = Field(description="Timestamp when the project was last updated")

class BaseModelWithTimestamps(BaseModel):
    """Base model providing common timestamp fields."""
    created_at: datetime = Field(description="Timestamp when the record was created")
    updated_at: datetime = Field(description="Timestamp when the record was last updated")

class ModuleModel(BaseModel):
    """Module definition for file operations."""
    name: str = Field(description="Full path of the module file")
    description: Optional[str] = Field(None, description="Description of the module's purpose")
    imports: List[FileImportModel] = Field(default_factory=list, description="Import statements in the module")

class CodebaseContextModel(BaseModel):
    """Code elements - functions, types, and constants - that pertain to a given task."""
    functions: List[str] = Field(default_factory=list, description="qualified function names to include in the context", examples=[["module1.function1", "module2.function2"]])
    types: List[str] = Field(default_factory=list, description="Type definition names (pydantic models) to include in the context", examples=["Type1Model", "Type2Model"])
    constants: List[str] = Field(default_factory=list, description="Existing named constants to include in the context", examples=["CONSTANT1", "CONSTANT2"])