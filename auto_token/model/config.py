from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .token import Token


class Config(BaseModel):
    log_level: str = "INFO"
    token_dir: Path = Path("~/.config/auto-token/tokens/")
    tokens: set[Token] = set()
