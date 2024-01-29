from __future__ import annotations

import enum

from pydantic import BaseModel


class EnvType(enum.Enum):
    env = "env"
    file = "file"


class Env(BaseModel):
    name: str
    type: EnvType = EnvType.env
    value: str

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Env) -> bool:
        return self.name == other.name and self.type == other.type


class Token(BaseModel):
    name: str
    active: bool = True
    envs: set[Env] = set()

    # experimental
    dependencies: set[str] = set()

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Token | str) -> bool:
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name and self.envs == other.envs
