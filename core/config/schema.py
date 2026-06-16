"""Pydantic v2 schema for the Testopus configuration (fail-fast validation).

Lenient by design (`extra="allow"`) so the config stays extensible per app; only the known,
load-bearing fields are validated. `core.config.config_loader` runs this so a malformed config
fails fast with a clear error instead of a cryptic ``KeyError`` deep inside a test.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ToolshopConfig(BaseModel):
    """The public Practice Software Testing ("Toolshop") demo target.

    One block drives both the web examples (``web_url``) and the API examples (``api_url``);
    ``email``/``password`` are the *public* demo account used by the login flows (defaulted in
    ``default.yaml`` via ``${VAR:-default}`` — overridable, never a secret).
    """

    model_config = ConfigDict(extra="allow")

    web_url: str
    api_url: str = ""
    email: str = ""
    password: str = ""


class Configuration(BaseModel):
    model_config = ConfigDict(extra="allow")

    toolshop: Optional[ToolshopConfig] = None


class RootConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    configuration: Optional[Configuration] = None
