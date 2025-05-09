import json
import subprocess
from pathlib import Path

def run_act(workflow_file: str, event: str = "push", event_data: dict = None) -> subprocess.CompletedProcess:
    """Run act on a specific workflow file."""
    if event_data is None:
        event_data = {
            "ref": "refs/tags/v0.3.25.beta1",
            "before": "0" * 40,
            "after": "1" * 40,
            "repository": {
                "name": "testing_actions",
                "full_name": "brittany.jones/testing_actions"
            },
            "pusher": {
                "name": "brittany.jones",
                "email": "brittany.jones@example.com"
            },
            "created": True,
            "deleted": False,
            "forced": False,
            "base_ref": None,
            "compare": "https://github.com/brittany.jones/testing_actions/compare/v0.3.25.beta1",
            "commits": [],
            "head_commit": None
        }

    # Create temporary event file
    event_file = Path("event.json")
    event_file.write_text(json.dumps(event_data))

    try:
        # Run act with the specified workflow
        result = subprocess.run(
            [
                "act",
                event,
                "-W",
                str(Path("..") / "workflows" / workflow_file),  # Updated path
                "--container-architecture",
                "linux/amd64",
                "--eventpath",
                "event.json",
                "--dry-run"  # Don't actually run the commands, just validate the workflow
            ],
            capture_output=True,
            text=True,
            check=False
        )
        return result
    finally:
        # Cleanup
        event_file.unlink()

def test_publish_pre_release_workflow():
    """Test the pre-release workflow."""
    result = run_act("publish-pre-release.yml")
    assert result.returncode == 0, f"Workflow validation failed: {result.stderr}"
    
    # Check that the workflow would run the expected steps
    assert "Run Set up Python" in result.stdout
    assert "Run Install uv" in result.stdout
    assert "Run Tests" in result.stdout
    assert "Run Build the artifact" in result.stdout
    assert "Run Publish to TestPyPI" in result.stdout
    assert "Run Create GitHub Release" in result.stdout

def test_publish_release_workflow():
    """Test the release workflow."""
    event_data = {
        "ref": "refs/tags/v0.3.25",
        "before": "0" * 40,
        "after": "1" * 40,
        "repository": {
            "name": "testing_actions",
            "full_name": "brittany.jones/testing_actions"
        },
        "pusher": {
            "name": "brittany.jones",
            "email": "brittany.jones@example.com"
        },
        "created": True,
        "deleted": False,
        "forced": False,
        "base_ref": None,
        "compare": "https://github.com/brittany.jones/testing_actions/compare/v0.3.25",
        "commits": [],
        "head_commit": None
    }
    
    result = run_act("publish-release.yml", event_data=event_data)
    assert result.returncode == 0, f"Workflow validation failed: {result.stderr}"
    
    # Check that the workflow would run the expected steps
    assert "Run Set up Python" in result.stdout
    assert "Run Install uv" in result.stdout
    assert "Run Tests" in result.stdout
    assert "Run Build the artifact" in result.stdout
    assert "Run Publish to PyPI" in result.stdout
    assert "Run Create GitHub Release" in result.stdout 
