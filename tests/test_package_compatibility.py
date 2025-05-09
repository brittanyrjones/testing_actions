import pytest
import sys
import io
import json
import urllib.request
from contextlib import redirect_stdout
from hello_world import say_hello
import subprocess
import os
from pathlib import Path

def get_available_versions():
    """Get the latest version from TestPyPI."""
    package_name = "bjones-testing-actions"
    url = f"https://test.pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            versions = sorted(data["releases"].keys())
            return [versions[-1]] if versions else []  # Return only the latest version
    except Exception as e:
        print(f"Error fetching versions: {e}")
        return []

def create_venv(venv_path):
    """Create a virtual environment at the specified path."""
    subprocess.run([
        sys.executable,
        "-m",
        "uv",
        "venv",
        str(venv_path)
    ], check=True)

    # Get the Python executable path for this venv
    if sys.platform == "win32":
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_path = os.path.join(venv_path, "bin", "python")

    return python_path

def install_version(version):
    """Install a specific version of the package from TestPyPI in a fresh venv."""
    # Create a temporary venv
    venv_path = Path(".venv-test")
    if venv_path.exists():
        import shutil
        shutil.rmtree(venv_path)

    python_path = create_venv(venv_path)

    # Install aiohttp first
    subprocess.run([
        sys.executable,
        "-m",
        "uv",
        "pip",
        "install",
        "--target",
        str(venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"),
        "aiohttp>=3.11.12"
    ], check=True)

    # Then install our package
    subprocess.run([
        sys.executable,
        "-m",
        "uv",
        "pip",
        "install",
        "--target",
        str(venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"),
        "--index-url",
        "https://test.pypi.org/simple/",
        "--extra-index-url",
        "https://pypi.org/simple/",
        "--index-strategy",
        "unsafe-best-match",
        f"bjones-testing-actions=={version}"
    ], check=True)

    return python_path

def run_test_in_venv(python_path, test_code):
    """Run test code in the virtual environment."""
    result = subprocess.run(
        [python_path, "-c", test_code],
        capture_output=True,
        text=True,
        check=False
    )
    return result

def cleanup_venv():
    """Clean up the temporary virtual environment."""
    venv_path = Path(".venv-test")
    if venv_path.exists():
        import shutil
        shutil.rmtree(venv_path)

def test_say_hello_output():
    """Test that say_hello() produces the expected output."""
    # Capture stdout
    f = io.StringIO()
    with redirect_stdout(f):
        say_hello()

    output = f.getvalue().strip()
    assert output == "Hello, world!, testing! again!"

def test_say_hello_return_type():
    """Test that say_hello() returns None (implicitly)."""
    result = say_hello()
    assert result is None

def test_say_hello_no_args():
    """Test that say_hello() doesn't accept any arguments."""
    with pytest.raises(TypeError):
        say_hello("test")

def test_say_hello_no_kwargs():
    """Test that say_hello() doesn't accept keyword arguments."""
    with pytest.raises(TypeError):
        say_hello(message="test")

def test_say_hello_import():
    """Test that say_hello can be imported directly."""
    from hello_world import say_hello as imported_say_hello
    assert imported_say_hello is say_hello

def test_say_hello_module_import():
    """Test that the module can be imported."""
    import hello_world
    assert hasattr(hello_world, 'say_hello')
    assert callable(hello_world.say_hello)

def uninstall_package():
    """Uninstall the package."""
    subprocess.run([sys.executable, "-m", "uv", "pip", "uninstall", "bjones-testing-actions"], check=True)

@pytest.mark.parametrize("version", get_available_versions())
def test_package_compatibility(version):
    """Test package compatibility with specific versions."""
    try:
        # Install specific version in a fresh venv
        python_path = install_version(version)

        # Test 1: Module structure and basic functionality
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
        result = run_test_in_venv(python_path, test_code)
        assert result.returncode == 0, f"Tests failed for version {version}:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    finally:
        # Clean up
        cleanup_venv()
        # Always uninstall the package after the test
        uninstall_package()
