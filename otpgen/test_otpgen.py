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
    """Run otpgen.sh with given arguments."""
    if env is None:
        env = TEST_ENV
    else:
        env = {**TEST_ENV, **env}

    try:
        return subprocess.run(
            ["./otpgen.sh"] + args,
            capture_output=True,
            text=True,
            env=env,
            check=False  # Don't raise exception on non-zero exit
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
    result = run_otpgen(["--install"])
    assert result.returncode == 0, f"Install failed: {result.stdout}"
    assert "Installation successful" in result.stdout

def test_list_key():
    """Test listing keys."""
    # First install
    run_otpgen(["--install"])
    result = run_otpgen(["--list-key"])
    assert result.returncode == 0, f"List key failed: {result.stdout}"
    assert "No 2FA found in keystore" in result.stdout

def test_run_otpgen_direct():
    """Test running otpgen.sh directly."""
    result = run_otpgen([])
    assert result.returncode == 0, f"Direct run failed: {result.stdout}"
    assert "otpgen.sh, otpgen:   2 Factor Authettication for Linux" in result.stdout
    assert "Features:" in result.stdout
    assert "Syntax:" in result.stdout

def test_generate_otp():
    """Test generating OTP."""
    # First install
    run_otpgen(["--install"])
    result = run_otpgen(["--gen-key", "1"])
    assert result.returncode == 255, f"Generate OTP failed: {result.stdout}"
    assert "Unable to generate 2FA token for ID: 1" in result.stdout

def test_clean_install():
    """Test clean installation."""
    # First install
    run_otpgen(["--install"])
    # Then try installing again
    # In CI mode, we expect it to fail since it requires user input
    result = run_otpgen(["--clean-install"])
    assert result.returncode == 1, f"Clean install failed: {result.stdout}"
    assert "This will remove all existing 2FA tokens!" in result.stdout

def strip_ansi(text):
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)