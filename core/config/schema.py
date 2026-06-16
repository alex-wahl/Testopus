"""Pydantic v2 schema for the Testopus configuration (fail-fast validation).

Lenient by design (`extra="allow"`) so the config stays extensible per app; only the known,
load-bearing fields are validated. `core.config.config_loader` runs this so a malformed config
fails fast with a clear error instead of a cryptic ``KeyError`` deep inside a test.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class GasagConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    web_url: str
    username: str = ""
    password: str = ""


class Configuration(BaseModel):
    model_config = ConfigDict(extra="allow")

    gasag: Optional[GasagConfig] = None


class RootConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    configuration: Optional[Configuration] = None
