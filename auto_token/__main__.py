from __future__ import annotations

from pathlib import Path

import toml
import typer
from loguru import logger
from pydantic import BaseModel
from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.style import Style
from rich.table import Table

from auto_token.model import Token
from auto_token.utils import prompt_env

app = typer.Typer()


class Config(BaseModel):
    log_level: str = "INFO"
    token_path: Path = Path("~/.config/auto-token/tokens/")
    tokens: set[Token] = set()


def init_logger(log_level: str):
    handler = RichHandler(console=Console(style=Style()), highlighter=NullHighlighter(), markup=True)
    logger.remove()
    logger.add(handler, format="{message}", level=log_level)


def get_config(config_path: Path, config_logger: bool = True) -> Config:
    config_path = config_path.expanduser()
    if not config_path.exists():
        if config_logger:
            init_logger("INFO")
        create_config = typer.confirm(
            f"Config file not found at {config_path}. Do you want to create it?",
        )
        config = Config()
        if create_config:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, mode="w") as f:
                toml.dump(config.model_dump(mode="json"), f)
            logger.info(f"Use default config and create config file at [bold purple]{config_path}[/].")
        else:
            logger.info("No config file found, use default config.")
    else:
        with open(config_path) as f:
            config = Config.model_validate(toml.load(f))
        if config_logger:
            init_logger(config.log_level)
        logger.info(f"Loaded config from [bold purple]{config_path}[/].")

    tokens_path = Path(config.token_path).expanduser()
    for token_path in tokens_path.iterdir():
        with open(token_path) as f:
            token = Token.model_validate(toml.load(f))
            if token in config.tokens:
                logger.warning(f"Token {token_path.name} already exists, will overwrite it.")
            config.tokens.add(token)

    return config


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
