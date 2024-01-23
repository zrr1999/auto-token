from typer.testing import CliRunner

from auto_token.__main__ import app

runner = CliRunner()


def test_app():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "All tokens" in result.stdout
