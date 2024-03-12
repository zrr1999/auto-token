from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, overload

import toml
import typer
from loguru import logger
from rich.console import Console
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.style import Style

from .model import Config, Env, EnvType, Token


def prompt_env(env_name: str, description: str | None = None, use_env: bool | None = None) -> Env:
    value = os.environ.get(env_name, None)
    if value is not None:
        if use_env is None:
            use_env = typer.confirm(f"Wheather to use {env_name} in env?", default=True)
        if use_env:
            return Env(name=env_name, type=EnvType.env, value=value)
    if description is None:
        description = f"Please input env {env_name} value"
    value = typer.prompt(description)
    return Env(name=env_name, type=EnvType.env, value=value)


def init_logger(log_level: str):
    handler = RichHandler(console=Console(style=Style()), highlighter=NullHighlighter(), markup=True)
    logger.remove()
    logger.add(handler, format="{message}", level=log_level)


def get_config(config_path: Path | str = "~/.config/auto-token/config.toml", config_logger: bool = True) -> Config:
    config_path = Path(config_path).expanduser()
    if not config_path.exists():
        if config_logger:
            init_logger("INFO")
        create_config = typer.confirm(
            f"Config file not found at {config_path}. Do you want to create it?", default=True
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

    tokens_path = Path(config.token_dir).expanduser()
    tokens_path.mkdir(parents=True, exist_ok=True)
    for token_path in tokens_path.iterdir():
        with open(token_path) as f:
            raw_dict = toml.load(f)
            raw_dict["name"] = token_path.stem
            token = Token.model_validate(raw_dict)
            if token in config.tokens:
                logger.warning(f"Token {token.name} already loaded from {token_path}, which will be ignored.")
            config.tokens.add(token)

    return config


def create_token(name: str) -> Token:
    token = Token(name=name, envs=set())
    while True:
        env_name = typer.prompt(f"Please input env name for {name} (empty to exit)", default="", show_default=False)
        if env_name == "":
            break
        env = prompt_env(env_name)
        token.envs.add(env)
    return token


def create_token_by_env(name: str, env_names: list[str]) -> Token:
    envs: set[Env] = set()
    for env_name in env_names:
        env = prompt_env(env_name, use_env=True)
        envs.add(env)
    return Token(name=name, envs=envs)


@overload
def get_token(name: str, config: Config, *, create: Literal[True]) -> Token:
    ...


@overload
def get_token(name: str, config: Config, *, create: Literal[False] = False) -> Token | None:
    ...


def get_token(name: str, config: Config, *, create: bool = False, env_names: list[str] | None = None):
    if env_names is None:
        env_names = []
    for token in config.tokens:
        if token.name == name:
            return token
    if create:
        token = create_token(name) if env_names is None else create_token_by_env(name, env_names)
        return token
    return None
