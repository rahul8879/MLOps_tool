from databricks.sdk import WorkspaceClient
from core.config import settings

_client = None

def get_databricks_client() -> WorkspaceClient:
    global _client
    if _client is None:
        _client = WorkspaceClient(
            host=settings.databricks_host,
            token=settings.databricks_token
        )
    return _client