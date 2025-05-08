import pytest
import sys
import io
from contextlib import redirect_stdout
from hello_world import say_hello

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
