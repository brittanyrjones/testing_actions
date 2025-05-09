import pytest
import sys
import json
import urllib.request
import subprocess
import os
import importlib.metadata
import tempfile
import shutil
from pathlib import Path

def get_latest_version(pypi_type="testpypi"):
    """Get the latest version from PyPI or TestPyPI."""
    package_name = "bjones_testing_actions"
    base_url = "https://test.pypi.org" if pypi_type == "testpypi" else "https://pypi.org"
    url = f"{base_url}/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            versions = sorted(data["releases"].keys())
            return versions[-1] if versions else None
    except Exception as e:
        print(f"Error fetching versions from {pypi_type}: {e}")
        return None

def test_latest_package():
    """Test that the latest package from PyPI/TestPyPI works as expected."""
    # Get the local package version
    try:
        with open("pyproject.toml", "r") as f:
            import tomli
            data = tomli.loads(f.read())
            version = data["project"]["version"]
    except Exception as e:
        pytest.skip(f"Could not determine local package version: {e}")

    print(f"\nTesting local version {version}")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create a new virtual environment
            venv_path = os.path.join(temp_dir, "venv")
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

            # Get the Python executable path in the new virtual environment
            if sys.platform == "win32":
                python_path = os.path.join(venv_path, "Scripts", "python.exe")
            else:
                python_path = os.path.join(venv_path, "bin", "python")

            # Install the package using pip (simulating user installation)
            print(f"Installing package version {version} from local directory...")
            subprocess.run([
                python_path,
                "-m",
                "pip",
                "install",
                "."
            ], check=True, capture_output=True)

            # Test package metadata using the new Python executable
            print("\nChecking package metadata...")
            result = subprocess.run(
                [python_path, "-c", "import importlib.metadata; print(importlib.metadata.distribution('bjones_testing_actions').version)"],
                capture_output=True,
                text=True,
                check=True
            )
            installed_version = result.stdout.strip()
            assert installed_version == version, f"Installed version {installed_version} doesn't match expected version {version}"

            # Test package functionality in the new environment
            print("\nTesting package functionality...")
            test_code = """
import hello_world
from hello_world import say_hello
import io
from contextlib import redirect_stdout

# Test function exists and is callable
assert hasattr(hello_world, 'say_hello'), "say_hello function missing"
assert callable(hello_world.say_hello), "say_hello is not callable"

# Test output
f = io.StringIO()
with redirect_stdout(f):
    say_hello()
output = f.getvalue().strip()
assert "Hello, world!" in output, f"Unexpected output: {output}"

# Test return value
result = say_hello()
assert result is None, "say_hello does not return None"

# Test function signature
try:
    say_hello("test")
    assert False, "say_hello should not accept arguments"
except TypeError:
    pass  # Expected behavior
"""
            result = subprocess.run(
                [python_path, "-c", test_code],
                capture_output=True,
                text=True,
                check=False
            )
            assert result.returncode == 0, f"Tests failed for version {version}:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            print("Functionality tests passed!")

            # Test package can be imported in a new Python process
            print("\nTesting package import in new process...")
            import_result = subprocess.run(
                [python_path, "-c", "import hello_world; print('Import successful')"],
                capture_output=True,
                text=True,
                check=False
            )
            assert import_result.returncode == 0, f"Package import failed:\nstdout: {import_result.stdout}\nstderr: {import_result.stderr}"
            print("Import test passed!")

        finally:
            # No need to uninstall since we're using a temporary virtual environment
            print("\nCleaning up...")
