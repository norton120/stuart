from click.testing import CliRunner
from stuart.cli import cli

def test_prompt_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['prompt', 'create a new project'], input='y\n')
        assert result.exit_code == 0
        assert "Executing prompt" in result.output
