# MCP-Dataiku

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes [Dataiku DSS](https://www.dataiku.com/) capabilities as tools for AI assistants such as Claude.

## Features

| Tool | Description |
|------|-------------|
| `list_projects` | List all accessible Dataiku projects |
| `list_datasets` | List datasets in a project |
| `get_dataset_schema` | Return the column schema of a dataset |
| `read_dataset` | Read rows from a dataset (up to a configurable limit) |
| `list_scenarios` | List scenarios in a project |
| `run_scenario` | Trigger a scenario and get the run ID |
| `get_scenario_last_run` | Get the outcome of the last scenario run |
| `list_recipes` | List recipes in a project |
| `list_jobs` | List recent build jobs in a project |
| `get_job_status` | Get the status and activity log of a job |

## Requirements

- Python 3.10+
- A running Dataiku DSS instance (version 13+)
- A Dataiku personal API key

## Installation

```bash
pip install mcp-dataiku
```

Or install from source:

```bash
git clone https://github.com/Velkasi/MCP-Dataiku.git
cd MCP-Dataiku
pip install -e .
```

## Configuration

Set the following environment variables (or place them in a `.env` file):

| Variable | Required | Description |
|----------|----------|-------------|
| `DATAIKU_HOST` | Yes | URL of your Dataiku DSS instance, e.g. `https://dss.example.com` |
| `DATAIKU_API_KEY` | Yes | Your Dataiku personal API key |
| `DATAIKU_DEFAULT_PROJECT` | No | Default project key used when a tool is called without an explicit `project_key` |

Example `.env`:

```env
DATAIKU_HOST=https://dss.example.com
DATAIKU_API_KEY=your_api_key_here
DATAIKU_DEFAULT_PROJECT=MY_PROJECT
```

## Usage

### As a CLI command

```bash
mcp-dataiku
```

The server communicates over **stdio** using the MCP protocol.

### With Claude Desktop

Add the following to your Claude Desktop MCP configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "dataiku": {
      "command": "mcp-dataiku",
      "env": {
        "DATAIKU_HOST": "https://dss.example.com",
        "DATAIKU_API_KEY": "your_api_key_here",
        "DATAIKU_DEFAULT_PROJECT": "MY_PROJECT"
      }
    }
  }
}
```

### With Claude Code (CLI)

```bash
claude mcp add dataiku -- mcp-dataiku
```

Then set the required environment variables in your shell or `.env` file.

## Tool Reference

### `list_projects`

Lists all Dataiku projects the API key has access to.

```json
{}
```

### `list_datasets`

```json
{
  "project_key": "MY_PROJECT"
}
```

### `get_dataset_schema`

```json
{
  "project_key": "MY_PROJECT",
  "dataset_name": "customers"
}
```

### `read_dataset`

```json
{
  "project_key": "MY_PROJECT",
  "dataset_name": "customers",
  "limit": 50
}
```

### `list_scenarios`

```json
{
  "project_key": "MY_PROJECT"
}
```

### `run_scenario`

```json
{
  "project_key": "MY_PROJECT",
  "scenario_id": "daily_refresh"
}
```

### `get_scenario_last_run`

```json
{
  "project_key": "MY_PROJECT",
  "scenario_id": "daily_refresh"
}
```

### `list_recipes`

```json
{
  "project_key": "MY_PROJECT"
}
```

### `list_jobs`

```json
{
  "project_key": "MY_PROJECT",
  "limit": 10
}
```

### `get_job_status`

```json
{
  "project_key": "MY_PROJECT",
  "job_id": "BUILD_customers_2024-01-01T00-00-00-000"
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

## License

MIT
