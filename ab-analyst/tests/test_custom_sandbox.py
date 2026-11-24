"""The managed sandbox tool is pinned to $AB_SANDBOX_ID and the model cannot choose a sandbox."""

import base64

from langchain_core.tools import StructuredTool

from agent.custom_sandbox import pin_to_custom_sandbox


def _fake(name: str, calls: list) -> StructuredTool:
    # Same argument names as the managed system.ai.sandbox run_code tool.
    async def _run(
        code: str = "", sandbox_id: str = "", language: str = "python", timeout_seconds: int = 120
    ):
        calls.append(
            (name, {"code": code, "sandbox_id": sandbox_id, "language": language,
                    "timeout_seconds": timeout_seconds})
        )
        return "ok"

    return StructuredTool.from_function(coroutine=_run, name=name, description=name)


def _managed_tools(calls):
    return [_fake("create_sandbox", calls), _fake("run_code", calls), _fake("delete_sandbox", calls)]


def test_no_env_keeps_template_behaviour(monkeypatch):
    monkeypatch.delenv("AB_SANDBOX_ID", raising=False)
    tools = _managed_tools([])
    assert pin_to_custom_sandbox(tools) == tools


async def test_pins_sandbox_and_hides_lifecycle_tools(monkeypatch):
    monkeypatch.setenv("AB_SANDBOX_ID", "ab-stats")
    calls: list = []
    tools = pin_to_custom_sandbox(_managed_tools(calls))

    assert [t.name for t in tools] == ["run_python"]
    # The model-facing schema has no sandbox_id or language: it cannot pick a sandbox.
    assert set(tools[0].args) == {"code", "timeout_seconds"}

    code = "print('quotes \"and\" \\\\ backslashes')"
    await tools[0].ainvoke({"code": code})

    (name, args), = calls
    assert name == "run_code"
    assert args["sandbox_id"] == "ab-stats"
    assert args["language"] == "sh"
    payload = args["code"].split("echo ")[1].split(" |")[0]
    assert base64.b64decode(payload).decode() == code
