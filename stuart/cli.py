from typing import Optional
import click
import logging
from click import style
from .prompts import edit_code
from .models import get_session, Project

logger = logging.getLogger(__name__)

class StuartCLI:
    """Main CLI handler for Stuart operations."""

    def __init__(self) -> None:
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the CLI."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def execute_prompt(self, prompt_text: str) -> None:
        """Execute the given prompt."""
        logger.debug("Processing prompt...")
        edit_code(prompt_text)
        click.echo("Processing...")

@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Stuart CLI - AI-driven code generation tool."""
    ctx.obj = StuartCLI()
    # Ensure a project exists for all commands except 'init'
    if ctx.invoked_subcommand != 'init':
        session = get_session()
        project = session.query(Project).first()
        if not project:
            click.echo("No project found. Please run 'stuart init' to create a project first.")
            ctx.exit(1)
        ctx.obj.project = project

@cli.command()
@click.argument('name', type=str)
@click.argument('primary_language', type=str, default="Python")
@click.pass_obj
def init(obj: StuartCLI, name: str, primary_language: str) -> None:
    """Initialize a new project."""
    logger.info("Initializing new project")
    session = get_session()
    project, created = Project.get_or_create(session, name=name, primary_programming_language=primary_language)
    if created:
        session.commit()
        click.echo(f"Project '{name}' created successfully.")
    else:
        click.echo(f"Project '{name}' already exists.")

@cli.command()
@click.argument('prompt_text', type=str)
@click.pass_context
def prompt(ctx: click.Context, prompt_text: str) -> None:
    """Execute a prompt-based task."""
    logger.info("Starting prompt execution")
    click.echo(f"Executing prompt: {prompt_text}")

    if click.confirm("Do you want to proceed?", default=True):
        try:
            ctx.obj.execute_prompt(prompt_text)
        except Exception as e:
            logger.error(f"Failed to process prompt: {e}", exc_info=True)
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

@cli.command()
@click.pass_context
def extract(ctx: click.Context) -> None:
    """Extract changes from the rendered package and apply them to the project."""
    logger.info("Extracting changes from the rendered package")
    session = get_session()
    project = ctx.obj.project

    for index, change in enumerate(project.extract_changes(session)):
        if "created" in change:
            click.echo(style(f"- {change}", fg="green"))
        else:
            click.echo(style(f"- {change}", fg="yellow"))

    if not index:
        click.echo("No changes detected.")
    else:
        click.echo(f"{index} changes applied successfully.")

def main() -> None:
    """Entry point for the CLI application."""
    cli(auto_envvar_prefix='STUART')

if __name__ == '__main__':
    main()
