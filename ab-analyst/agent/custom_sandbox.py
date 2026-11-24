"""Pin the managed ``system.ai.sandbox`` tool to one pre-built, custom-image sandbox.

``agentbricks tools add sandbox`` gives the agent three MCP tools: ``create_sandbox``, ``run_code``
and ``delete_sandbox``. Left alone, the model creates throwaway sandboxes from the default image.
This module instead:

* hides ``create_sandbox`` / ``delete_sandbox`` so the model cannot spin up or remove sandboxes;
* replaces ``run_code`` with ``run_python``, which always targets ``AB_SANDBOX_ID`` (a sandbox you
  created from your own Artifact Registry image) and runs the code with the image's ``python3``.

The sandbox ID is set server-side (env var), never chosen by the model. Calls still go through the
managed MCP tool, so identity, auth and the ``agent.toml`` policy are unchanged.
"""

from __future__ import annotations

import base64
import os

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

SANDBOX_ID_ENV = "AB_SANDBOX_ID"
_HIDDEN = {"create_sandbox", "delete_sandbox"}


class RunPythonArgs(BaseModel):
    code: str = Field(description="A complete, self-contained Python 3.12 script. Print results.")
    timeout_seconds: int = Field(default=120, ge=1, le=600)


def _shell_for(code: str) -> str:
    # Ship the script base64-encoded so quotes, heredocs and backslashes in the model's code
    # survive the trip through the shell untouched.
    payload = base64.b64encode(code.encode()).decode()
    return f"cd /tmp && echo {payload} | base64 -d > cell.py && python3 cell.py"


def _pinned_run_python(run_code: BaseTool, sandbox_id: str) -> BaseTool:
    async def run_python(code: str, timeout_seconds: int = 120):
        return await run_code.ainvoke(
            {
                "sandbox_id": sandbox_id,
                "language": "sh",
                "code": _shell_for(code),
                "timeout_seconds": timeout_seconds,
            }
        )

    return StructuredTool.from_function(
        coroutine=run_python,
        name="run_python",
        description=(
            "Run a Python script in the team's statistics sandbox. Python 3.12 with pinned "
            "packages: pandas 3.1, numpy 2.5, scipy 1.18, statsmodels 0.15, pingouin 0.7, "
            "duckdb 1.5, matplotlib 3.11. These are newer than many examples you know: print a "
            "result's columns before indexing into it (pingouin uses snake_case, e.g. 'cohen_d'). "
            "Unity Catalog volumes are readable under /Volumes. Each call is a fresh process: "
            "re-load data in every script and print everything you need."
        ),
        args_schema=RunPythonArgs,
    )


def pin_to_custom_sandbox(tools: list[BaseTool]) -> list[BaseTool]:
    """Return ``tools`` with the managed sandbox tools pinned to ``$AB_SANDBOX_ID``.

    No-op when the env var is unset, so the template's default behaviour is preserved.
    """
    sandbox_id = os.getenv(SANDBOX_ID_ENV)
    if not sandbox_id:
        return tools
    pinned: list[BaseTool] = []
    for tool in tools:
        if tool.name in _HIDDEN:
            continue
        pinned.append(_pinned_run_python(tool, sandbox_id) if tool.name == "run_code" else tool)
    return pinned
