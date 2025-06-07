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
    "DEBIAN_FRONTEND": "noninteractive",  # Prevent interactive prompts
    **os.environ
}

def run_otpgen(args, env=None, input_text=None):
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
            env=env
        )

        if input_text:
            stdout, stderr = process.communicate(input=input_text)
        else:
            stdout, stderr = process.communicate()

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

def test_install():
    """Test installation."""
    # Provide password input for installation
    result = run_otpgen(["--install"], input_text="Test@123\nTest@123\n")
    assert result.returncode == 0, f"Install failed: {result.stdout}"
    assert "Installation successful" in result.stdout

def test_list_key():
    """Test listing keys."""
    # First install with password
    run_otpgen(["--install"], input_text="Test@123\nTest@123\n")
    # List keys with password
    result = run_otpgen(["--list-key"], input_text="Test@123\n")
    assert result.returncode == 0, f"List key failed: {result.stdout}"
    assert "No 2FA found in keystore" in result.stdout

def test_run_otpgen_direct():
    """Test running otpgen.sh directly."""
    # First install with password to ensure we have a valid environment
    run_otpgen(["--install"], input_text="Test@123\nTest@123\n")
    # Run without arguments, should show help
    result = run_otpgen([], input_text="Test@123\n")
    assert result.returncode == 0, f"Direct run failed: {result.stdout}"
    # Check for any of these strings in the output
    assert any(text in result.stdout for text in [
        "otpgen.sh, otpgen:   2 Factor Authettication for Linux",
        "Features:",
        "Syntax:",
        "Usage:"
    ]), f"Unexpected output: {result.stdout}"

def test_generate_otp():
    """Test generating OTP."""
    # First install with password
    run_otpgen(["--install"], input_text="Test@123\nTest@123\n")
    # Try to generate OTP with password
    result = run_otpgen(["--gen-key", "1"], input_text="Test@123\n")
    assert result.returncode == 255, f"Generate OTP failed: {result.stdout}"
    assert "Unable to generate 2FA token for ID: 1" in result.stdout

def test_clean_install():
    """Test clean installation."""
    # First install with password
    run_otpgen(["--install"], input_text="Test@123\nTest@123\n")
    # Try clean install with password
    result = run_otpgen(["--clean-install"], input_text="Test@123\n")
    assert result.returncode == 0, f"Clean install failed: {result.stdout}"
    assert "Installation successful" in result.stdout

def strip_ansi(text):
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)