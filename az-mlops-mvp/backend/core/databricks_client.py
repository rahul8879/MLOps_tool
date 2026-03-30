"""
core/databricks_client.py
=========================
Singleton Databricks WorkspaceClient factory.

Every service module imports `get_workspace_client()` to get the shared
instance — we never instantiate WorkspaceClient more than once per process.

If DATABRICKS_HOST / DATABRICKS_TOKEN are not set (local dev), the function
returns None and the service layer falls back to mock data automatically.

Usage:
    from core.databricks_client import get_workspace_client
    client = get_workspace_client()          # WorkspaceClient | None
"""

import logging
from typing import Optional

from core.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton
_workspace_client = None
_initialised = False


def get_workspace_client():
    """
    Return the singleton WorkspaceClient, initialising it on first call.
    Returns None if credentials are not configured (triggers mock fallback).
    """
    global _workspace_client, _initialised

    if _initialised:
        return _workspace_client

    _initialised = True

    if settings.use_mock_data:
        logger.warning(
            "[Databricks] DATABRICKS_HOST or DATABRICKS_TOKEN not set. "
            "Running in MOCK mode — all Databricks calls return dummy data."
        )
        _workspace_client = None
        return None

    try:
        from databricks.sdk import WorkspaceClient

        _workspace_client = WorkspaceClient(
            host=settings.DATABRICKS_HOST,
            token=settings.DATABRICKS_TOKEN,
        )
        logger.info(
            "[Databricks] WorkspaceClient initialised for host: %s",
            settings.DATABRICKS_HOST,
        )
    except Exception as exc:
        logger.error(
            "[Databricks] Failed to initialise WorkspaceClient: %s. "
            "Falling back to MOCK mode.",
            exc,
        )
        _workspace_client = None

    return _workspace_client


def reset_client():
    """
    Reset the singleton — used in tests to force re-initialisation.
    """
    global _workspace_client, _initialised
    _workspace_client = None
    _initialised = False
