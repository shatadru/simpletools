import os
import sys
import pytest
import subprocess
from pathlib import Path
import re

# Test environment variables
TEST_ENV = {
    "OTPGEN_PASSWORD": "Test@123",
    "DYLD_LIBRARY_PATH": "/usr/local/lib:/opt/homebrew/lib",
    "LD_LIBRARY_PATH": "/usr/local/lib:/opt/homebrew/lib",
    "CI": "true"  # Indicate we're running in CI
}

def run_otpgen(args, env=None):
    """Run otpgen.py with given arguments and environment."""
    if env is None:
        env = {}

    # Merge with test environment
    full_env = os.environ.copy()
    full_env.update(TEST_ENV)
    full_env.update(env)

    # Run the script
    result = subprocess.run(
        [sys.executable, "otpgen.py"] + args,
        env=full_env,
        capture_output=True,
        text=True
    )
    return result

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test artifacts after each test."""
    yield
    # Clean up test artifacts
    home = Path.home()
    test_files = [
        home / "otpgen",
        home / ".otpgen",
        home / "otpgen" / ".secret_list",
        home / "otpgen" / ".check_update"
    ]
    for file in test_files:
        if file.exists():
            if file.is_dir():
                for item in file.glob("*"):
                    item.unlink()
                file.rmdir()
            else:
                file.unlink()

def test_help():
    """Test help command."""
    result = run_otpgen(["--help"])
    assert result.returncode == 0
    assert "Usage:" in result.stdout

def test_install():
    """Test installation."""
    result = run_otpgen(["--install"], env=TEST_ENV)
    assert result.returncode == 0
    assert "Installation successful" in result.stdout
    assert (Path.home() / "otpgen").exists()

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_generate_test_qr():
    """Test QR code generation."""
    result = run_otpgen(["--generate-test-qr"])
    assert result.returncode == 0
    assert "Test QR code generated" in result.stdout
    assert (Path.home() / "otpgen" / "test_qr.png").exists()

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_add_key():
    """Test adding a key."""
    # First install
    run_otpgen(["--install"], env=TEST_ENV)
    # Generate test QR
    run_otpgen(["--generate-test-qr"])
    # Add key
    result = run_otpgen(["--add-key", str(Path.home() / "otpgen" / "test_qr.png")], env=TEST_ENV)
    assert result.returncode == 0
    assert "Key added successfully" in result.stdout

def test_list_key():
    """Test listing keys."""
    # First install
    run_otpgen(["--install"], env=TEST_ENV)

    result = run_otpgen(["--list-key"], env=TEST_ENV)
    assert result.returncode == 0
    assert "No 2FA found in keystore" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_gen_key():
    """Test generating OTP."""
    # First install and add a key
    run_otpgen(["--install"], env=TEST_ENV)
    run_otpgen(["--generate-test-qr"])
    run_otpgen(["--add-key", str(Path.home() / "otpgen" / "test_qr.png")], env=TEST_ENV)

    result = run_otpgen(["--gen-key", "1"], env=TEST_ENV)
    assert result.returncode == 0
    assert "OTP:" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_remove_key():
    """Test removing a key."""
    # First install and add a key
    run_otpgen(["--install"], env=TEST_ENV)
    run_otpgen(["--generate-test-qr"])
    run_otpgen(["--add-key", str(Path.home() / "otpgen" / "test_qr.png")], env=TEST_ENV)

    result = run_otpgen(["--remove-key", "1"], env=TEST_ENV)
    assert result.returncode == 0
    assert "Key removed successfully" in result.stdout

def test_clean_install():
    """Test clean installation."""
    # First install
    run_otpgen(["--install"], env=TEST_ENV)
    # Then try installing again
    result = run_otpgen(["--clean-install"], env=TEST_ENV)
    assert result.returncode == 0
    assert "Installation successful" in result.stdout

def test_print_python_env():
    """Test Python environment printing."""
    result = run_otpgen(["--print-python-env"])
    assert result.returncode == 0
    assert "Python Environment:" in result.stdout
    assert "sys.executable:" in result.stdout
    assert "sys.path:" in result.stdout

def test_run_otpgen_direct():
    """Test running otpgen.py directly."""
    result = subprocess.run(
        [sys.executable, "otpgen.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout

def test_generate_otp():
    """Test OTP generation"""
    # First install
    run_otpgen(["--install"], env=TEST_ENV)

    result = run_otpgen(["--gen-key", "1"], env=TEST_ENV)
    assert result.returncode == 255  # Expected to fail when no keys exist
    assert "Unable to generate 2FA token" in result.stdout

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)