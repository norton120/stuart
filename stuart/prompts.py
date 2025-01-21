from logging import getLogger
from requests import get, HTTPError
from stuart.typing import PypiPackage

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