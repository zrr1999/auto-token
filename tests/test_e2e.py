from __future__ import annotations

import pytest
from typer.testing import CliRunner

from auto_token.__main__ import app

runner = CliRunner()


@pytest.mark.benchmark
def test_e2e():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, f"Exit code was {result.exit_code}, expected 0. Error: {result.exc_info}"
    assert "All tokens" in result.stdout, f"Output was {result.stdout}, expected 'All tokens'"
