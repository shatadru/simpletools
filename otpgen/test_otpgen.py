import os
import sys
import pytest
import subprocess
from pathlib import Path
import re

# Test configuration
TEST_PASSWORD = "Test@123"
TEST_ENV = {
    "OTPGEN_PASSWORD": TEST_PASSWORD,
    "DYLD_LIBRARY_PATH": "/opt/homebrew/lib",  # For macOS
    "LD_LIBRARY_PATH": "/usr/local/lib",       # For Linux
}

def run_otpgen(args, env=None):
    """Run otpgen.py with given arguments and environment."""
    cmd = [sys.executable, "otpgen.py"] + args
    env = env or {}
    full_env = os.environ.copy()
    full_env.update(env)
    result = subprocess.run(cmd, env=full_env, capture_output=True, text=True)
    return result

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test artifacts after each test."""
    yield
    # Remove test QR code
    try:
        Path("test_qr.png").unlink()
    except FileNotFoundError:
        pass
    # Remove keystore
    keystore = Path.home() / "otpgen"
    if keystore.exists():
        for file in keystore.glob("*"):
            file.unlink()
        keystore.rmdir()

def test_help():
    """Test help command."""
    result = run_otpgen(["--help"])
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()

def test_install():
    """Test installation."""
    result = run_otpgen(["--install"], env=TEST_ENV)
    assert result.returncode == 0
    assert "Keystore created successfully" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_generate_test_qr():
    """Test QR code generation."""
    result = run_otpgen(["generate_test_qr.py"])
    assert result.returncode == 0
    assert Path("test_qr.png").exists()

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_add_key():
    """Test adding a key from QR code."""
    # First generate a test QR code
    run_otpgen(["generate_test_qr.py"])
    # Then add it
    result = run_otpgen(["--add-key", "test_qr.png"], env=TEST_ENV)
    assert result.returncode == 0
    assert "Key added successfully" in result.stdout

def test_list_key():
    """Test listing keys."""
    result = run_otpgen(["--list-key"], env=TEST_ENV)
    assert result.returncode == 0
    assert "No keys found" in result.stdout or "Key" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_gen_key():
    """Test generating OTP."""
    # First add a test key
    run_otpgen(["generate_test_qr.py"])
    run_otpgen(["--add-key", "test_qr.png"], env=TEST_ENV)
    # Then generate OTP
    result = run_otpgen(["--gen-key", "1"], env=TEST_ENV)
    assert result.returncode == 0
    assert "OTP copied to clipboard" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_remove_key():
    """Test removing a key."""
    # First add a test key
    run_otpgen(["generate_test_qr.py"])
    run_otpgen(["--add-key", "test_qr.png"], env=TEST_ENV)
    # Then remove it
    result = run_otpgen(["--remove-key", "1"], env=TEST_ENV)
    assert result.returncode == 0
    assert "Key removed successfully" in result.stdout

def test_clean_install():
    """Test clean installation."""
    # First install
    run_otpgen(["--install"], env=TEST_ENV)
    # Then try installing again
    result = run_otpgen(["--install"], env=TEST_ENV)
    assert result.returncode == 0
    assert "Keystore already exists" in result.stdout

def test_print_python_env():
    import sys
    import json
    import subprocess
    code = (
        "import sys, json; print(json.dumps({'executable': sys.executable, 'path': sys.path}))"
    )
    result = subprocess.run(['python3', '-c', code], capture_output=True, text=True)
    print('PYTHON ENV:', result.stdout)
    assert result.returncode == 0

def test_run_otpgen_direct():
    import subprocess
    result = subprocess.run(['python3', 'otpgen.py', '--help'], capture_output=True, text=True)
    print('DIRECT STDOUT:', result.stdout)
    print('DIRECT STDERR:', result.stderr)
    print('DIRECT EXIT CODE:', result.returncode)
    assert result.returncode == 0

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def test_generate_otp():
    """Test OTP generation"""
    code, out, err = run_otpgen(['--gen-key', '1'])
    out_clean = strip_ansi(out)
    assert code == 0
    assert 'Success: OTP:' in out_clean
    assert 'Success: OTP has been copied to clipboard' in out_clean