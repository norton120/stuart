from typing import List
from logging import getLogger
from requests import get, HTTPError
from pathlib import Path
from stuart.typing import PypiPackage, FileImportModel, FunctionModel
from stuart.models import File, FNode, FileImport, Base, get_session

logger = getLogger(__name__)

"""Handles all prompts and tools for LLM generation."""

"""Guidelines
- Only use stateless, atomic functions.
- Always type function arguments and return values.
- Include comprehensive but brief docstrings for every function.

"""

def get_pypi_package(package_name: str) -> PypiPackage:
    """
    Fetch package information from PyPI API.

    Args:
        package_name: Name of the Python package to lookup

    Returns:
        PypiPackage object containing package details

    Raises:
        HTTPError: If the PyPI API request fails
        KeyError: If the package is not found or response is malformed
    """
    logger.info("Fetching PyPI package info for %s", package_name)

    try:
        response = get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status()
        data = response.json()

        package = PypiPackage(
            name=data["info"]["name"],
            version=data["info"]["version"],
            description=data["info"]["summary"]
        )
        logger.debug("Successfully fetched package info for %s", package_name)
        return package

    except HTTPError as e:
        logger.error("Failed to fetch PyPI package %s: %s", package_name, str(e))
        raise
    except KeyError as e:
        logger.error("Invalid response format for package %s: %s", package_name, str(e))
        raise

def _upsert_function(
    session: "Session",
    module_path: str | Path,
    function_name: str,
    imports: List[FileImportModel],
    description: str,
    return_type: str,
    code: str
) -> FunctionModel:
    """Internal implementation of upsert_function with session management."""
    logger.info("Upserting function %s in module %s", function_name, module_path)

    # Normalize path and use as name for file lookup
    module_path = Path(module_path)
    if not str(module_path).endswith('.py'):
        module_path = module_path.with_suffix('.py')

    # Get or create file using module_path as name
    file, _ = File.get_or_create(
        session,
        name=str(module_path),
        suffix='.py',
        description=f"Module containing {function_name}"
    )

    for import_ in imports:
        file.imports.append(
            FileImport(
                imported=import_.imported,
                from_path=import_.from_path,
                alias=import_.alias
            ))

    # Update function using combination of file_id and name
    function, _ = FNode.upsert(
        session,
        name=function_name,
        file_id=file.id,
        description=description,
        body=code,
        return_type=return_type
    )

    session.commit()

    return FunctionModel(
        name=function.name,
        description=function.description,
        body=function.body,
        return_type=function.return_type
    )

def upsert_function(
    module_path: str | Path,
    function_name: str,
    imports: List[FileImportModel],
    description: str,
    return_type: str,
    code: str
) -> FunctionModel:
    """
    Create or update a function definition in the specified module.

    Args:
        module_path: Path to the module containing the function
        function_name: Name of the function to create/update
        imports: List of imports required by the function
        description: Function docstring/description
        return_type: Return type annotation for the function
        code: Function implementation code

    Returns:
        FunctionModel representing the created/updated function

    Raises:
        ValueError: If module path or function name is invalid
    """
    with get_session() as session:
        return _upsert_function(
            session=session,
            module_path=module_path,
            function_name=function_name,
            imports=imports,
            description=description,
            return_type=return_type,
            code=code
        )