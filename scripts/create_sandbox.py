"""Create a Databricks Sandbox from a custom Artifact Registry image and smoke-test it.

Usage: DATABRICKS_CONFIG_PROFILE=<profile> python create_sandbox.py <sandbox_id> <image_uri>
"""
import sys
import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sandbox import EnvironmentSpec, Sandbox, SandboxSpec
from google.protobuf.duration_pb2 import Duration

sandbox_id, image_uri = sys.argv[1], sys.argv[2]
w = WorkspaceClient()

t0 = time.time()
sb = w.sandbox.create_sandbox(
    sandbox=Sandbox(
        display_name="A/B test analyst (stats stack)",
        spec=SandboxSpec(environment=EnvironmentSpec(image_uri=image_uri)),
    ),
    sandbox_id=sandbox_id,
)
print("created", sb.name)

while (state := w.sandbox.get_sandbox(sb.name).status.state.value) != "SANDBOX_STATE_RUNNING":
    print(f"  {time.time() - t0:5.0f}s  {state}")
    time.sleep(5)
print(f"running after {time.time() - t0:.0f}s")

probe = (
    "grep PRETTY_NAME /etc/os-release; ldd --version | head -1; python3 --version; "
    "python3 -c 'import scipy, statsmodels, pingouin, duckdb; "
    "print(\"scipy\", scipy.__version__, \"| statsmodels\", statsmodels.__version__, "
    "\"| pingouin\", pingouin.__version__, \"| duckdb\", duckdb.__version__)'"
)
r = w.sandbox.execute_command_sync(
    sb.name, "/bin/bash", args=["-c", probe], execution_timeout=Duration(seconds=60)
)
print("exit", r.exit_code)
print(r.stdout)
if r.stderr:
    print("stderr:", r.stderr)
