from contextlib import asynccontextmanager

from fastapi import FastAPI

from .logger import get_logger
from .oauth import create_sso_client, load_sso_metadata
from .state import State


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger()
    logger.info("Starting up...")

    sso_client = create_sso_client()

    sso_metadata = await load_sso_metadata(sso_client)
    logger.info(f"SSO metadata loaded: {sso_metadata}")

    yield State(logger=logger, sso_metadata=sso_metadata, sso_client=sso_client)

    await sso_client.aclose()
    logger.info("Shutting down...")
