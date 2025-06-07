import os
import sys
import pytest
import subprocess
from pathlib import Path
import re
import signal
import tempfile

# Test environment
TEST_ENV = {
    "OTPGEN_PASSWORD": "Test@123",
    "CI": "true",  # Set CI=true to avoid interactive prompts
    "DEBIAN_FRONTEND": "noninteractive",  # Prevent interactive prompts
    **os.environ
}

def run_otpgen(args, env=None, input_text=None, timeout=10):
    """Run otpgen.sh with given arguments."""
    if env is None:
        env = TEST_ENV
    else:
        env = {**TEST_ENV, **env}

    try:
        process = subprocess.Popen(
            ["./otpgen.sh"] + args,
            stdin=subprocess.PIPE if input_text else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            preexec_fn=os.setsid  # Create new process group
        )

        try:
            if input_text:
                stdout, stderr = process.communicate(input=input_text, timeout=timeout)
            else:
                stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Kill the process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds")

        return subprocess.CompletedProcess(
            args=["./otpgen.sh"] + args,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
    except subprocess.CalledProcessError as e:
        return e

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
        if test_dir.is_dir():
            test_dir.rmdir()

def test_help():
    """Test help command."""
    result = run_otpgen(["--help"])
    assert result.returncode == 0, f"Help command failed: {result.stdout}"
    assert "otpgen.sh, otpgen:   2 Factor Authettication for Linux" in result.stdout
    assert "Syntax:" in result.stdout
    assert "-V, --version" in result.stdout
    assert "-i, --install" in result.stdout

def test_version():
    """Test version command."""
    result = run_otpgen(["--version"])
    assert result.returncode == 0, f"Version command failed: {result.stdout}"
    assert "Version:" in result.stdout
    # Extract version number and verify format
    version_match = re.search(r"Version:\s*(\d+\.\d+(?:-\d+)?)", result.stdout)
    assert version_match, "Version number not found in output"
    version = version_match.group(1)
    assert re.match(r"^\d+\.\d+(?:-\d+)?$", version), f"Invalid version format: {version}"

def test_install():
    """Test installation."""
    # Test with valid password
    result = run_otpgen(["--install"], input_text="Test@123\nTest@123\n")
    assert result.returncode == 0, f"Install failed: {result.stdout}"
    assert "Installation successful" in result.stdout

    # Test with invalid password (too short)
    result = run_otpgen(["--install"], input_text="test\ntest\n")
    assert result.returncode == 1, f"Install with weak password should fail: {result.stdout}"
    assert "Password is too short" in result.stdout

def test_list_key():
    """Test listing keys."""
    # First install with password
    run_otpgen(["--install"], input_text="Test@123\nTest@123\n")

    # List keys with correct password
    result = run_otpgen(["--list-key"], input_text="Test@123\n")
    assert result.returncode == 0, f"List key failed: {result.stdout}"
    assert "No 2FA found in keystore" in result.stdout

    # List keys with incorrect password
    result = run_otpgen(["--list-key"], input_text="WrongPass\n")
    assert result.returncode == 1, f"List key with wrong password should fail: {result.stdout}"
    assert "Invalid password" in result.stdout

def test_run_otpgen_direct():
    """Test running otpgen.sh directly."""
    # Check if script is executable
    assert os.access("./otpgen.sh", os.X_OK), "otpgen.sh is not executable"

    # Run with --version to avoid interactive prompts
    result = run_otpgen(["--version"])
    assert result.returncode == 0, f"Version check failed: {result.stdout}"
    assert "Version:" in result.stdout

    # Run with invalid argument
    result = run_otpgen(["--invalid-arg"])
    assert result.returncode == 1, f"Invalid argument should fail: {result.stdout}"
    assert "Unknown option" in result.stdout

def test_generate_otp():
    """Test generating OTP."""
    # First install with password
    run_otpgen(["--install"], input_text="Test@123\nTest@123\n")

    # Try to generate OTP with non-existent ID
    result = run_otpgen(["--gen-key", "999"], input_text="Test@123\n")
    assert result.returncode == 1, f"Generate OTP with invalid ID should fail: {result.stdout}"
    assert "Unable to generate 2FA token for ID: 999" in result.stdout

    # Try to generate OTP with invalid password
    result = run_otpgen(["--gen-key", "1"], input_text="WrongPass\n")
    assert result.returncode == 1, f"Generate OTP with wrong password should fail: {result.stdout}"
    assert "Invalid password" in result.stdout

def test_clean_install():
    """Test clean installation."""
    # First install with password
    run_otpgen(["--install"], input_text="Test@123\nTest@123\n")

    # In CI mode, we expect clean install to fail since it requires user input
    result = run_otpgen(["--clean-install"])
    assert result.returncode == 1, f"Clean install failed: {result.stdout}"
    assert "This will remove all existing 2FA tokens!" in result.stdout

def test_invalid_qr_code():
    """Test handling of invalid QR code."""
    # First install with password
    run_otpgen(["--install"], input_text="Test@123\nTest@123\n")

    # Create a temporary invalid QR code file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        temp_file.write(b'invalid qr code data')
        temp_file_path = temp_file.name

    try:
        # Try to add invalid QR code
        result = run_otpgen(["--add-key", temp_file_path], input_text="Test@123\n")
        assert result.returncode == 1, f"Adding invalid QR code should fail: {result.stdout}"
        assert "Failed to detect usable QR Code" in result.stdout
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

def strip_ansi(text):
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)