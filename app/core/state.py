from logging import Logger
from typing import TypedDict

import httpx

from .oauth import OpenIDConfiguration


class State(TypedDict):
    logger: Logger
    sso_metadata: OpenIDConfiguration
    sso_client: httpx.AsyncClient
