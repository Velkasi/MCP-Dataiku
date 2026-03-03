"""Configuration for the Dataiku MCP server."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class DataikuConfig:
    """Dataiku DSS connection configuration."""

    host: str
    api_key: str
    project_key: str | None = None

    @classmethod
    def from_env(cls) -> "DataikuConfig":
        """Load configuration from environment variables.

        Required environment variables:
            DATAIKU_HOST: URL of the Dataiku DSS instance (e.g. https://dss.example.com)
            DATAIKU_API_KEY: Personal API key for authentication

        Optional environment variables:
            DATAIKU_DEFAULT_PROJECT: Default project key to use when none is specified
        """
        host = os.environ.get("DATAIKU_HOST", "")
        api_key = os.environ.get("DATAIKU_API_KEY", "")
        project_key = os.environ.get("DATAIKU_DEFAULT_PROJECT")

        if not host:
            raise ValueError(
                "DATAIKU_HOST environment variable is required. "
                "Set it to your Dataiku DSS instance URL."
            )
        if not api_key:
            raise ValueError(
                "DATAIKU_API_KEY environment variable is required. "
                "Set it to your Dataiku personal API key."
            )

        return cls(host=host.rstrip("/"), api_key=api_key, project_key=project_key)
