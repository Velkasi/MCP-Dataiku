"""Dataiku DSS API client wrapper."""

from __future__ import annotations

import json
from typing import Any

import dataikuapi

from .config import DataikuConfig


class DataikuClient:
    """Thin wrapper around the Dataiku API client."""

    def __init__(self, config: DataikuConfig) -> None:
        self.config = config
        self._client = dataikuapi.DSSClient(config.host, config.api_key)

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def list_projects(self) -> list[dict[str, Any]]:
        """Return summary info for all accessible projects."""
        projects = self._client.list_projects()
        return [
            {
                "project_key": p["projectKey"],
                "name": p.get("name", p["projectKey"]),
                "description": p.get("description", ""),
                "creation_date": p.get("creationTag", {}).get("lastModifiedOn"),
            }
            for p in projects
        ]

    def get_project(self, project_key: str) -> dataikuapi.DSSProject:
        return self._client.get_project(project_key)

    # ------------------------------------------------------------------
    # Datasets
    # ------------------------------------------------------------------

    def list_datasets(self, project_key: str) -> list[dict[str, Any]]:
        """Return summary info for all datasets in a project."""
        project = self.get_project(project_key)
        datasets = project.list_datasets()
        return [
            {
                "name": d["name"],
                "type": d.get("type", ""),
                "managed": d.get("managed", False),
                "tags": d.get("tags", []),
            }
            for d in datasets
        ]

    def read_dataset(
        self,
        project_key: str,
        dataset_name: str,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Read rows from a dataset and return as a list of records."""
        project = self.get_project(project_key)
        dataset = project.get_dataset(dataset_name)
        schema = dataset.get_schema()
        columns = [col["name"] for col in schema.get("columns", [])]

        rows: list[dict[str, Any]] = []
        with dataset.get_dataframe_iterator(limit=limit) as it:
            for chunk in it.iter_dataframes(chunksize=limit):
                for _, row in chunk.iterrows():
                    rows.append(row.to_dict())
                break  # only first chunk needed given the limit

        return {"columns": columns, "rows": rows, "total_returned": len(rows)}

    def get_dataset_schema(self, project_key: str, dataset_name: str) -> dict[str, Any]:
        """Return the schema of a dataset."""
        project = self.get_project(project_key)
        dataset = project.get_dataset(dataset_name)
        return dataset.get_schema()

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------

    def list_scenarios(self, project_key: str) -> list[dict[str, Any]]:
        """Return summary info for all scenarios in a project."""
        project = self.get_project(project_key)
        scenarios = project.list_scenarios()
        return [
            {
                "id": s["id"],
                "name": s.get("name", s["id"]),
                "type": s.get("type", ""),
                "active": s.get("active", False),
            }
            for s in scenarios
        ]

    def run_scenario(self, project_key: str, scenario_id: str) -> dict[str, Any]:
        """Trigger a scenario run and return the run details."""
        project = self.get_project(project_key)
        scenario = project.get_scenario(scenario_id)
        run = scenario.run()
        return {
            "run_id": run.run_id,
            "scenario_id": scenario_id,
            "project_key": project_key,
            "status": "RUNNING",
        }

    def get_scenario_last_run(
        self, project_key: str, scenario_id: str
    ) -> dict[str, Any]:
        """Return details about the last run of a scenario."""
        project = self.get_project(project_key)
        scenario = project.get_scenario(scenario_id)
        settings = scenario.get_settings()
        last_run = scenario.get_last_finished_run()
        if last_run is None:
            return {"scenario_id": scenario_id, "last_run": None}
        run_details = last_run.get_details()
        return {
            "scenario_id": scenario_id,
            "run_id": last_run.run_id,
            "outcome": run_details.get("scenarioRun", {}).get("result", {}).get("outcome"),
            "start": run_details.get("scenarioRun", {}).get("start"),
            "end": run_details.get("scenarioRun", {}).get("end"),
        }

    # ------------------------------------------------------------------
    # Recipes
    # ------------------------------------------------------------------

    def list_recipes(self, project_key: str) -> list[dict[str, Any]]:
        """Return summary info for all recipes in a project."""
        project = self.get_project(project_key)
        recipes = project.list_recipes()
        return [
            {
                "name": r["name"],
                "type": r.get("type", ""),
                "inputs": r.get("inputs", {}),
                "outputs": r.get("outputs", {}),
            }
            for r in recipes
        ]

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

    def list_jobs(self, project_key: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent jobs in a project."""
        project = self.get_project(project_key)
        jobs = project.list_jobs()
        result = []
        for j in jobs[:limit]:
            result.append(
                {
                    "job_id": j.get("def", {}).get("id", ""),
                    "type": j.get("def", {}).get("type", ""),
                    "state": j.get("state", ""),
                    "start_time": j.get("startTime"),
                }
            )
        return result

    def get_job_status(self, project_key: str, job_id: str) -> dict[str, Any]:
        """Return the current status of a job."""
        project = self.get_project(project_key)
        job = project.get_job(job_id)
        status = job.get_status()
        return {
            "job_id": job_id,
            "state": status.get("state", ""),
            "start_time": status.get("startTime"),
            "end_time": status.get("endTime"),
            "activities": [
                {
                    "name": a.get("name"),
                    "state": a.get("state"),
                    "error": a.get("error"),
                }
                for a in status.get("activities", [])
            ],
        }
