import pytest
import sys
import json
import urllib.request
import subprocess
import os
from pathlib import Path
import importlib.metadata
import tempfile
import shutil

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
    pypi_type = os.getenv("PYPI_TYPE", "testpypi")
    version = get_latest_version(pypi_type)
    if not version:
        pytest.skip(f"No versions found on {pypi_type}")
    
    print(f"\nTesting version {version} from {pypi_type}")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Install the package using pip (simulating user installation)
            print(f"Installing package version {version} from {pypi_type}...")
            base_url = "https://test.pypi.org/simple/" if pypi_type == "testpypi" else "https://pypi.org/simple/"
            extra_url = "https://pypi.org/simple/" if pypi_type == "testpypi" else "https://test.pypi.org/simple/"
            
            subprocess.run([
                sys.executable,
                "-m",
                "pip",
                "install",
                "--index-url",
                base_url,
                "--extra-index-url",
                extra_url,
                f"bjones_testing_actions=={version}"
            ], check=True, capture_output=True)

            # Test package metadata
            print("\nChecking package metadata...")
            dist = importlib.metadata.distribution("bjones_testing_actions")
            installed_version = dist.version
            assert installed_version == version, f"Installed version {installed_version} doesn't match expected version {version}"
            
            # Test package dependencies
            print("\nChecking package dependencies...")
            requires = [str(r) for r in dist.requires]
            print(f"Package requires: {requires}")
            
            # Test package functionality in a clean environment
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
                [sys.executable, "-c", test_code],
                capture_output=True,
                text=True,
                check=False
            )
            assert result.returncode == 0, f"Tests failed for version {version}:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            print("Functionality tests passed!")
            
            # Test package can be imported in a new Python process
            print("\nTesting package import in new process...")
            import_result = subprocess.run(
                [sys.executable, "-c", "import hello_world; print('Import successful')"],
                capture_output=True,
                text=True,
                check=False
            )
            assert import_result.returncode == 0, f"Package import failed:\nstdout: {import_result.stdout}\nstderr: {import_result.stderr}"
            print("Import test passed!")
            
            # Run the package's test suite
            print("\nRunning package test suite...")
            
            # Copy tests from current directory
            tests_dir = os.path.join(os.path.dirname(__file__))
            shutil.copytree(tests_dir, os.path.join(temp_dir, "tests"))
            
            # Install test dependencies
            subprocess.run([
                sys.executable,
                "-m",
                "pip",
                "install",
                "pytest>=8.0.0",
                "pytest-cov>=4.1.0"
            ], check=True, capture_output=True)
            
            # Run the tests
            test_result = subprocess.run(
                [sys.executable, "-m", "pytest", os.path.join(temp_dir, "tests"), "-v"],
                capture_output=True,
                text=True,
                check=False
            )
            assert test_result.returncode == 0, f"Package test suite failed:\nstdout: {test_result.stdout}\nstderr: {test_result.stderr}"
            print("Package test suite passed!")
            
        finally:
            # Uninstall the package
            print("\nCleaning up...")
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "bjones_testing_actions"], check=True) 
