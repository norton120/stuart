from os import environ
import json
from typing import List, TYPE_CHECKING
from logging import getLogger
from requests import get, HTTPError
from pathlib import Path
from langfuse.openai import openai
from langfuse.decorators import observe
from promptic import Promptic

from stuart.typing import PypiPackage, FileImportModel, FunctionModel, ModuleModel, CodebaseContextModel
from stuart.models import File, FNode, FileImport, get_session, Project


"""
() generation
-> single
=> loop
[ ] process
< > bool

ask -> (break ask into ordered tasks) => code task -> (generate context) -> context -> (generate code) => code
[ test code ] -> < failure? > (break code into code tasks) ^
"""



client = openai.OpenAI(
  api_key=environ.get("TOGETHER_API_KEY"),
  base_url="https://api.together.xyz/v1",
)

promptic = Promptic(openai_client=client)


if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = getLogger(__name__)

"""Handles all prompts and tools for LLM generation."""

"""Guidelines
- Only use stateless, atomic functions.
- Always type function arguments and return values.
- Include comprehensive but brief docstrings for every function.

"""

def generate_tasks(ask: str, project: Project) -> List[str]:
    """Breaks down the ask into ordered tasks"""
    @observe
    @promptic.llm(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            system=f"""Break the users request into very detailed and totally self-contained software programming CODING tasks, to be completed by a coding robot.

Here are details of the project in question:
name: {project.name}
description: {project.description}
current_state: {project.current_state}
primary_programming_language: {project.primary_programming_language}

Finally, return the list of tasks as JSON list of objects with keys title and body for each task ticket.
    """
    )
    def break_ask_into_ordered_tasks(ask: str):
        """{ask}"""

    raw_with_thoughts = break_ask_into_ordered_tasks(ask)
    json_ = raw_with_thoughts.split("```json")[1].split("```")[0]
    tasks = json.loads(json_)
    for task in tasks:
        ## for each task, complete the entire cycle.
        # 1. generate context
        context = generate_context_for_task(task["title"], project)
        # 2. generate the code changes
        code = generate_code_for_task(task["title"], context)
        # 3. render the codebase
        project.render_package()
        # 4. run localized tests, fix if they fail
        while not project.run_tests(code):
            subcode = generate_code_for_task(task["title"], context)
        # 5. refactor the codebase
        project.refactor_package(code)
        project.render_package(subcode)

def generate_context_for_task(task: str, project:"Project") -> dict:
    """gets the context elements for the given task"""
    @observe
    @promptic.llm(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            system="""
    // given the assigned task and the function tree, select which functions, schemas, and constants (if any) would be relevant to the task
    """
    )
    def select_context(task: str) -> CodebaseContextModel:
        """task: {task}

        tree:
        """ + project.tree




@observe
@promptic.llm(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        system="""
// general directions
// code rules
// tree output
// code for code in selected_functions


""",
)
def cycle(ask: str):
    """{ask}"""

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
    file_name: str,
    function_name: str,
    imports: List[str],
    description: str,
    return_type: str,
    code: str
) -> None:
    """Internal implementation of upsert_function with session management."""
    logger.info("Upserting function %s in module %s", function_name, file_name)

    # Get or create file using module_path as name
    file, _ = File.get_or_create(
        session,
        name=file_name.strip()
    )

    for import_ in imports:
        import_ = FileImport(**import_.model_dump())
        file.imports.append(import_)

    # Update function using combination of file_id and name
    function_, _ = FNode.upsert(
        session,
        name=function_name,
        file_id=file.id,
        description=description,
        body=code,
        return_type=return_type
    )

    session.commit()
    session.refresh(function_)
    return function_


@cycle.tool
def create_or_edit_function(
    file_name: str | Path,
    function_name: str,
    imports: List[str],  # Changed from List[FileImportModel] to List[dict]
    description: str,
    return_type: str,
    code: str
) -> FNode:
    """
    Create or update a function definition in the specified module.

    Args:
        file_name: the file where this function is defined
        function_name: the name of the function being created/updated
        imports: List of strings containing import statements your function needs
        description: the description of the function
        return_type: Return type annotation for the function
        code: the definition (source code) of the function

    Raises:
        ValueError: If the function definition is invalid
    """
    import_models = [i for imp in imports for i in FileImportModel.from_string(imp)]

    with get_session() as session:
        return _upsert_function(
            session=session,
            module_path=file_name,
            function_name=function_name,
            imports=import_models,
            description=description,
            return_type=return_type,
            code=code
        )

