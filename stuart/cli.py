import click

class StuartCLI:
    """Main CLI handler for Stuart operations."""

    def __init__(self):
        pass

@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Stuart CLI - AI-driven code generation tool."""
    ctx.obj = StuartCLI()

@cli.command()
@click.argument('name')
def hello(name: str) -> None:
    """Say hello to someone."""
    click.echo(f"Hello, {name}!")

if __name__ == '__main__':
    cli()
