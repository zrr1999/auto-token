from __future__ import annotations

from pathlib import Path

import toml
import typer
from loguru import logger
from rich import print
from rich.columns import Columns
from rich.table import Table

from auto_token.model import Token
from auto_token.utils import get_config, init_logger, prompt_env

app = typer.Typer()


@app.command("list")
def list_token(config_path: Path = Path("~/.config/auto-token/config.toml"), log_level: str = typer.Option(None)):
    config_logger = log_level is None
    if not config_logger:
        init_logger(log_level)
    config = get_config(config_path, config_logger=config_logger)

    table = Table(title="All tokens", min_width=40)
    table.add_column("Name")
    table.add_column("State")
    table.add_column("Envs")
    for token in config.tokens:
        envs = Columns(e.name for e in token.envs)
        table.add_row(token.name, str(token.active), envs, end_section=True)
    print(table)


@app.command("add")
def add_token(
    name: str, config_path: Path = Path("~/.config/auto-token/config.toml"), log_level: str = typer.Option(None)
):
    config_logger = log_level is None
    if not config_logger:
        init_logger(log_level)
    config = get_config(config_path, config_logger=config_logger)

    if name in config.tokens:
        logger.warning(f"Token {name} already exists, will overwrite it. (Ctrl+C to exit)")

    tokens_path = Path(config.token_path).expanduser()

    token = Token(name=name, envs=set())
    while True:
        env_name = typer.prompt(f"Please input env name for {name} (empty to exit)", default="", show_default=False)
        if env_name == "":
            break
        env = prompt_env(env_name)
        token.envs.add(env)

    with open(tokens_path / f"{name}.toml", mode="w") as f:
        toml.dump(token.model_dump(mode="json"), f)


@app.command()
def shellenv(config_path: Path = Path("~/.config/auto-token/config.toml")):
    logger.remove()
    config = get_config(config_path, config_logger=False)

    for token in config.tokens:
        if token.active:
            for env in token.envs:
                print(f'export {env.name}="{env.value}"')


if __name__ == "__main__":
    app()
