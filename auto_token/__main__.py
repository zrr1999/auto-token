from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import overload

import toml
import typer
from loguru import logger
from rich import print
from rich.columns import Columns
from rich.table import Table

from auto_token.model import Env, EnvType, Token
from auto_token.utils import create_token, get_config, get_token, init_logger

app = typer.Typer()


@overload
def update_token_command(func: None = None) -> Callable[[Callable], Callable[..., None]]:
    pass


@overload
def update_token_command(func: Callable) -> Callable[..., None]:
    pass


def update_token_command(func: Callable | None = None) -> Callable[..., Callable[..., None]] | Callable[..., None]:
    if func is None:
        return update_token_command

    def wrapper(
        name: str,
        config_path: Path = Path("~/.config/auto-token/config.toml"),
        log_level: str = typer.Option(None),
        operate_on_base: bool = False,
    ):
        config_logger = log_level is None
        if not config_logger:
            init_logger(log_level)

        if name == "base" and not operate_on_base:
            logger.error("You can't operate on base token.")
            raise typer.Exit(1)

        config = get_config(config_path, config_logger=config_logger)
        token = get_token(name, config)

        if token is None:
            logger.error(f"Token {name} not exists, please add it first.")
            raise typer.Exit(1)

        func(token)

        token_path = Path(config.token_dir).expanduser() / f"{token.name}.toml"

        if not token_path.exists():
            logger.warning(
                f"Token {name} exists, but token file not found, which may be created manually. Please check."
            )

        with open(token_path, mode="w") as f:
            toml.dump(token.model_dump(mode="json"), f)

    wrapper.__name__ = func.__name__
    return wrapper


@app.command()
def init(config_path: Path = Path("~/.config/auto-token/config.toml"), log_level: str = typer.Option(None)):
    name = "base"
    config_logger = log_level is None
    if not config_logger:
        init_logger(log_level)
    config = get_config(config_path, config_logger=config_logger)

    if name in config.tokens:
        logger.warning("Base already exists, will overwrite it. (Ctrl+C to exit)")

    token_dir = Path(config.token_dir).expanduser()
    token = Token(
        name=name, envs={Env(name="AUTO_TOKEN_ENV_DIR", type=EnvType.env, value=config.env_dir.expanduser().as_posix())}
    )
    with open(token_dir / f"{name}.toml", mode="w") as f:
        toml.dump(token.model_dump(mode="json"), f)


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

    token_dir = Path(config.token_dir).expanduser()
    token = create_token(name)
    with open(token_dir / f"{name}.toml", mode="w") as f:
        toml.dump(token.model_dump(mode="json"), f)


@app.command()
@update_token_command()
def enable(
    token: Token,
):
    if token.active:
        logger.warning(f"Token {token.name} already enabled.")
    else:
        token.active = True


@app.command()
@update_token_command()
def disable(
    token: Token,
):
    if not token.active:
        logger.warning(f"Token {token.name} already disabled.")
    else:
        token.active = False


@app.command()
@update_token_command()
def rename(
    token: Token,
):
    new_name = typer.prompt("Please input new name", default=token.name, show_default=False)
    token.name = new_name


@app.command()
def shellenv(config_path: Path = Path("~/.config/auto-token/config.toml")):
    logger.remove()
    config = get_config(config_path, config_logger=False)

    for token in config.tokens:
        if token.active:
            for env in token.envs:
                print(f"export {env.name}={env.value}")


@app.command()
def dumpenv(config_path: Path = Path("~/.config/auto-token/config.toml")):
    logger.remove()
    config = get_config(config_path, config_logger=False)
    env_dir = config.env_dir.expanduser()
    env_dir.expanduser().mkdir(parents=True, exist_ok=True)

    for token in config.tokens:
        with open(env_dir / f"{token.name}.env", "w") as f:
            for env in token.envs:
                f.write(f"{env.name}={env.value}\n")


if __name__ == "__main__":
    app()
