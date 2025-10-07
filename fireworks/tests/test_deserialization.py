"""Tests for deserialization failures and DB env var override behavior."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pytest

from fireworks.core.firework import Firework, Workflow
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import launch_rocket

if TYPE_CHECKING:
    from collections.abc import Generator

TESTDB_NAME = "fireworks_unittest"


@pytest.fixture(autouse=True)
def lpad() -> Generator[LaunchPad, None, None]:
    """Create a clean test database, yield LaunchPad, then drop the database."""
    try:
        lp = LaunchPad(name=TESTDB_NAME, strm_lvl="ERROR")
        lp.reset(password="1970-01-01", require_password=False)
    except Exception:
        pytest.skip("MongoDB is not running in localhost:27017! Skipping tests.")

    yield lp

    lp.connection.drop_database(TESTDB_NAME)


class FakeBadTask:
    """Minimal task-like stub whose serialization points to a non-existent class/module."""

    def to_dict(self) -> dict[str, Any]:
        """Return a bogus `_fw_name` that will fail deserialization."""
        return {"_fw_name": "totally.invalid.module::Nope"}


def test_fizzle_on_deserialization_failure(lpad: LaunchPad, tmp_path) -> None:
    """Test basic deserialization failure handling.

    Verifies that a FW whose task cannot be deserialized is marked FIZZLED and that
    exception details are recorded in the spec for debugging. Tests firework-level behavior.
    """
    # Create a Firework whose task serializes to a bogus _fw_name so recursive_deserialize fails
    fw = Firework(tasks=[FakeBadTask()], name="bad-deser-fw")
    wf = Workflow.from_firework(fw)
    lpad.add_wf(wf)

    # Run a rocket; it should attempt checkout, fail to deserialize, mark FIZZLED, and continue without raising
    # Use a temporary working directory
    os.chdir(tmp_path)
    ran = launch_rocket(lpad)
    # no runnable jobs after fizzling this FW
    assert ran is False

    fw_dict = lpad.get_fw_dict_by_id(1)
    assert fw_dict["state"] == "FIZZLED"
    # ensure exception details were recorded for debugging
    assert "_exception_details" in fw_dict["spec"]


def test_queue_skips_bad_and_runs_next(lpad: LaunchPad, tmp_path) -> None:
    """Test queue behavior with deserialization failures.

    Verifies that if the top-priority FW fails to deserialize, it is marked as FIZZLED
    and the queue doesn't get stuck—it moves on to process the next available FW.
    Ensures the queue remains operational despite bad FWs.
    """
    # Bad FW with higher priority
    bad_fw = Firework(tasks=[FakeBadTask()], name="bad-first", spec={"_priority": 100})
    # Good FW with no tasks (completes immediately) and lower priority
    good_fw = Firework(tasks=[], name="good-second", spec={"_priority": 1})

    lpad.add_wf(Workflow.from_firework(bad_fw))
    lpad.add_wf(Workflow.from_firework(good_fw))

    os.chdir(tmp_path)
    ran = launch_rocket(lpad)
    # First run fizzles the bad FW and doesn't run anything
    assert ran is False
    # Second run should pick up and complete the good FW
    ran = launch_rocket(lpad)

    bad = lpad.get_fw_dict_by_id(1)
    good = lpad.get_fw_dict_by_id(2)
    assert bad["state"] == "FIZZLED"
    assert good["state"] == "RESERVED"


def test_workflow_state_updated_on_deserialization_failure(lpad: LaunchPad, tmp_path) -> None:
    """Test database consistency after deserialization failures.

    Verifies that when a FW fails deserialization, the workflow collection is properly updated
    with both workflows.state="FIZZLED" and workflows.fw_states.{fw_id}="FIZZLED".
    Uses direct MongoDB queries (not LaunchPad API) to ensure _refresh_wf() correctly updates
    both fields, preventing database inconsistencies.
    """
    # Create a bad FW that will fail deserialization
    bad_fw = Firework(tasks=[FakeBadTask()], name="bad-deser-fw")
    wf = Workflow.from_firework(bad_fw)
    lpad.add_wf(wf)

    # Get the actual fw_id assigned by the database
    fw_dict = lpad.get_fw_dict_by_id(1)
    fw_id = fw_dict["fw_id"]

    # Attempt to launch - this should fail deserialization and mark as FIZZLED
    os.chdir(tmp_path)
    ran = launch_rocket(lpad)
    assert ran is False

    # Verify the FW is FIZZLED
    fw_dict = lpad.get_fw_dict_by_id(fw_id)
    assert fw_dict["state"] == "FIZZLED"

    # Verify the workflow document has been properly updated
    wf_doc = lpad.workflows.find_one({"nodes": fw_id})
    assert wf_doc is not None, "Workflow document should exist"

    # Check that workflow state is FIZZLED
    assert wf_doc["state"] == "FIZZLED", "Workflow state should be FIZZLED"

    # Check that fw_states mapping is updated for this fw_id
    fw_states_key = str(fw_id)  # MongoDB stores dict keys as strings
    assert fw_states_key in wf_doc["fw_states"], f"fw_states should contain key for fw_id {fw_id}"
    assert wf_doc["fw_states"][fw_states_key] == "FIZZLED", f"fw_states.{fw_id} should be FIZZLED"
