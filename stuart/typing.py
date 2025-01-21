from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

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