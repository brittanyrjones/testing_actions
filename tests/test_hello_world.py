import io
from contextlib import redirect_stdout
from hello_world import say_hello

def test_say_hello():
    """Test the say_hello function directly."""
    # Test output
    f = io.StringIO()
    with redirect_stdout(f):
        say_hello()
    output = f.getvalue().strip()
    assert "Hello, world!" in output, f"Unexpected output: {output}"

    # Test return value
    result = say_hello()
    assert result is None, "say_hello should not return None"

    # Test function signature
    try:
        say_hello("test")  # type: ignore
        assert False, "say_hello should not accept arguments"
    except TypeError:
        pass  # Expected behavior
