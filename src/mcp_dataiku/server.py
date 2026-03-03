"""MCP server entry point for Dataiku DSS."""

from __future__ import annotations

import json
import sys
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from .client import DataikuClient
from .config import DataikuConfig


def _json(obj: Any) -> str:
    """Serialize an object to a pretty-printed JSON string."""
    return json.dumps(obj, indent=2, default=str, ensure_ascii=False)


def _resolve_project(
    args: dict[str, Any],
    config: DataikuConfig,
    required: bool = True,
) -> str | None:
    """Return the project key from tool args or the default config."""
    key = args.get("project_key") or config.project_key
    if required and not key:
        raise ValueError(
            "No project_key provided and DATAIKU_DEFAULT_PROJECT is not set."
        )
    return key


def create_server() -> tuple[Server, DataikuClient]:
    """Instantiate the MCP server and Dataiku client."""
    config = DataikuConfig.from_env()
    client = DataikuClient(config)
    server = Server("mcp-dataiku")

    # ------------------------------------------------------------------
    # Tool definitions
    # ------------------------------------------------------------------

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="list_projects",
                description="List all Dataiku DSS projects accessible with the configured API key.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="list_datasets",
                description="List all datasets in a Dataiku project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key (e.g. MY_PROJECT). "
                            "Falls back to DATAIKU_DEFAULT_PROJECT env var.",
                        }
                    },
                },
            ),
            types.Tool(
                name="get_dataset_schema",
                description="Return the column schema of a Dataiku dataset.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key.",
                        },
                        "dataset_name": {
                            "type": "string",
                            "description": "Name of the dataset.",
                        },
                    },
                    "required": ["dataset_name"],
                },
            ),
            types.Tool(
                name="read_dataset",
                description="Read rows from a Dataiku dataset and return them as JSON records.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key.",
                        },
                        "dataset_name": {
                            "type": "string",
                            "description": "Name of the dataset to read.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (default 100).",
                            "default": 100,
                        },
                    },
                    "required": ["dataset_name"],
                },
            ),
            types.Tool(
                name="list_scenarios",
                description="List all scenarios in a Dataiku project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key.",
                        }
                    },
                },
            ),
            types.Tool(
                name="run_scenario",
                description="Trigger a Dataiku scenario run. Returns immediately with the run ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key.",
                        },
                        "scenario_id": {
                            "type": "string",
                            "description": "ID of the scenario to run.",
                        },
                    },
                    "required": ["scenario_id"],
                },
            ),
            types.Tool(
                name="get_scenario_last_run",
                description="Get the result of the last completed run of a Dataiku scenario.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key.",
                        },
                        "scenario_id": {
                            "type": "string",
                            "description": "ID of the scenario.",
                        },
                    },
                    "required": ["scenario_id"],
                },
            ),
            types.Tool(
                name="list_recipes",
                description="List all recipes in a Dataiku project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key.",
                        }
                    },
                },
            ),
            types.Tool(
                name="list_jobs",
                description="List recent jobs in a Dataiku project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of jobs to return (default 20).",
                            "default": 20,
                        },
                    },
                },
            ),
            types.Tool(
                name="get_job_status",
                description="Get the current status and activities of a Dataiku build job.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "Dataiku project key.",
                        },
                        "job_id": {
                            "type": "string",
                            "description": "ID of the job.",
                        },
                    },
                    "required": ["job_id"],
                },
            ),
        ]

    # ------------------------------------------------------------------
    # Tool handlers
    # ------------------------------------------------------------------

    @server.call_tool()
    async def call_tool(
        name: str,
        arguments: dict[str, Any],
    ) -> list[types.TextContent]:
        try:
            result = _dispatch(name, arguments, client, config)
            return [types.TextContent(type="text", text=_json(result))]
        except Exception as exc:  # noqa: BLE001
            return [
                types.TextContent(
                    type="text",
                    text=_json({"error": str(exc), "tool": name}),
                )
            ]

    return server, client


def _dispatch(
    name: str,
    args: dict[str, Any],
    client: DataikuClient,
    config: DataikuConfig,
) -> Any:
    """Route a tool call to the appropriate client method."""
    if name == "list_projects":
        return client.list_projects()

    if name == "list_datasets":
        project_key = _resolve_project(args, config)
        return client.list_datasets(project_key)

    if name == "get_dataset_schema":
        project_key = _resolve_project(args, config)
        dataset_name = args["dataset_name"]
        return client.get_dataset_schema(project_key, dataset_name)

    if name == "read_dataset":
        project_key = _resolve_project(args, config)
        dataset_name = args["dataset_name"]
        limit = int(args.get("limit", 100))
        return client.read_dataset(project_key, dataset_name, limit)

    if name == "list_scenarios":
        project_key = _resolve_project(args, config)
        return client.list_scenarios(project_key)

    if name == "run_scenario":
        project_key = _resolve_project(args, config)
        scenario_id = args["scenario_id"]
        return client.run_scenario(project_key, scenario_id)

    if name == "get_scenario_last_run":
        project_key = _resolve_project(args, config)
        scenario_id = args["scenario_id"]
        return client.get_scenario_last_run(project_key, scenario_id)

    if name == "list_recipes":
        project_key = _resolve_project(args, config)
        return client.list_recipes(project_key)

    if name == "list_jobs":
        project_key = _resolve_project(args, config)
        limit = int(args.get("limit", 20))
        return client.list_jobs(project_key, limit)

    if name == "get_job_status":
        project_key = _resolve_project(args, config)
        job_id = args["job_id"]
        return client.get_job_status(project_key, job_id)

    raise ValueError(f"Unknown tool: {name}")


async def _run() -> None:
    server, _ = create_server()
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-dataiku",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )


def main() -> None:
    """Entry point for the mcp-dataiku command."""
    import asyncio

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
