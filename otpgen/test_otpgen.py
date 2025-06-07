import os
import sys
import pytest
import subprocess
from pathlib import Path
import re

# Test environment
TEST_ENV = {
    "OTPGEN_PASSWORD": "Test@123",
    "CI": "true",  # Set CI=true to avoid interactive prompts
    **os.environ
}

def run_otpgen(args, env=None):
    """Run otpgen.py with given arguments."""
    if env is None:
        env = TEST_ENV
    else:
        env = {**TEST_ENV, **env}

    return subprocess.run(
        ["python", "otpgen.py"] + args,
        capture_output=True,
        text=True,
        env=env
    )

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test artifacts after each test."""
    yield
    # Clean up test artifacts
    test_dir = Path.home() / "otpgen"
    if test_dir.exists():
        for file in test_dir.glob("*"):
            if file.is_file():
                file.unlink()
        test_dir.rmdir()

def test_help():
    """Test help command."""
    result = run_otpgen(["--help"])
    assert result.returncode == 0
    assert "Usage:" in result.stdout

def test_install():
    """Test installation."""
    result = run_otpgen(["--install"])
    assert result.returncode == 0
    assert "Installation successful" in result.stdout

def test_list_key():
    """Test listing keys."""
    # First install
    run_otpgen(["--install"])
    result = run_otpgen(["--list-key"])
    assert result.returncode == 0
    assert "No 2FA found in keystore" in result.stdout

def test_run_otpgen_direct():
    """Test running otpgen.py directly."""
    result = run_otpgen([])
    assert result.returncode == 0
    assert "Usage:" in result.stdout

def test_generate_otp():
    """Test generating OTP without QR support."""
    # First install
    run_otpgen(["--install"])
    result = run_otpgen(["--gen-key", "1"])
    assert result.returncode == 255  # Should fail since no keys exist
    assert "Unable to generate 2FA token for ID: 1" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_generate_test_qr():
    """Test QR code generation."""
    result = run_otpgen(["--generate-test-qr"])
    assert result.returncode == 0
    assert "Test QR code generated" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_add_key():
    """Test adding a key."""
    # First install
    run_otpgen(["--install"])
    # Generate test QR
    run_otpgen(["--generate-test-qr"])
    # Add key
    result = run_otpgen(["--add-key", str(Path.home() / "otpgen" / "test_qr.png")])
    assert result.returncode == 0
    assert "New 2FA added successfully" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_gen_key():
    """Test generating OTP."""
    # First install and add a key
    run_otpgen(["--install"])
    run_otpgen(["--generate-test-qr"])
    run_otpgen(["--add-key", str(Path.home() / "otpgen" / "test_qr.png")])

    result = run_otpgen(["--gen-key", "1"])
    assert result.returncode == 0
    assert "OTP:" in result.stdout

@pytest.mark.skipif(not os.environ.get("WITH_QR"), reason="QR support not enabled")
def test_remove_key():
    """Test removing a key."""
    # First install and add a key
    run_otpgen(["--install"])
    run_otpgen(["--generate-test-qr"])
    run_otpgen(["--add-key", str(Path.home() / "otpgen" / "test_qr.png")])

    result = run_otpgen(["--remove-key", "1"])
    assert result.returncode == 0
    assert "2FA removed successfully" in result.stdout

def test_clean_install():
    """Test clean installation."""
    # First install
    run_otpgen(["--install"])
    # Then try installing again with non-interactive mode
    result = run_otpgen(["--clean-install", "--non-interactive"])
    assert result.returncode == 0
    assert "Installation successful" in result.stdout

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)