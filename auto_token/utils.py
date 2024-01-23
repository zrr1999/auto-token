from __future__ import annotations

import os

import typer

from .model import Env, EnvType


def prompt_env(env_name: str, description: str | None = None) -> Env:
    value = os.environ.get(env_name, None)
    if value is not None:
        use_env = typer.confirm(
            f"Wheather to use {env_name} in env?",
        )
        if use_env:
            return Env(name=env_name, type=EnvType.env, value=value)
    if description is None:
        description = f"Please input env {env_name} value"
    value = typer.prompt(description)
    return Env(name=env_name, type=EnvType.env, value=value)
