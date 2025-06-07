#!/usr/bin/env python3
"""Tests for enhanced OTP Generator features."""

import os
import json
import pytest
import tempfile
from pathlib import Path
from otpgen import OTPGenerator

# Test data
TEST_PASSWORD = "Test@123"
TEST_TOKENS = [
    {
        "secret": "JBSWY3DPEHPK3PXP",
        "issuer": "TestIssuer",
        "account": "test@example.com",
        "type": "totp",
        "counter": 0
    },
    {
        "secret": "JBSWY3DPEHPK3PXP",
        "issuer": "TestIssuer2",
        "account": "test2@example.com",
        "type": "hotp",
        "counter": 0
    }
]

@pytest.fixture
def otp_generator():
    """Create a temporary OTP generator instance."""
    with tempfile.TemporaryDirectory() as temp_dir:
        otp = OTPGenerator(base_dir=temp_dir)
        yield otp

def test_install(otp_generator):
    """Test installation."""
    otp_generator.install(TEST_PASSWORD)
    assert otp_generator.keystore_file.exists()
    assert otp_generator.backup_dir.exists()

def test_add_token(otp_generator):
    """Test adding tokens."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    # Add TOTP token
    otp_generator.add_token(
        TEST_TOKENS[0]["secret"],
        TEST_TOKENS[0]["issuer"],
        TEST_TOKENS[0]["account"],
        TEST_TOKENS[0]["type"]
    )

    # Add HOTP token
    otp_generator.add_token(
        TEST_TOKENS[1]["secret"],
        TEST_TOKENS[1]["issuer"],
        TEST_TOKENS[1]["account"],
        TEST_TOKENS[1]["type"],
        TEST_TOKENS[1]["counter"]
    )

    tokens = otp_generator.list_tokens()
    assert len(tokens) == 2
    assert tokens[0]["issuer"] == TEST_TOKENS[0]["issuer"]
    assert tokens[1]["issuer"] == TEST_TOKENS[1]["issuer"]

def test_duplicate_token(otp_generator):
    """Test adding duplicate token."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    otp_generator.add_token(
        TEST_TOKENS[0]["secret"],
        TEST_TOKENS[0]["issuer"],
        TEST_TOKENS[0]["account"],
        TEST_TOKENS[0]["type"]
    )

    with pytest.raises(ValueError, match="Token already exists"):
        otp_generator.add_token(
            TEST_TOKENS[0]["secret"],
            TEST_TOKENS[0]["issuer"],
            TEST_TOKENS[0]["account"],
            TEST_TOKENS[0]["type"]
        )

def test_generate_otp(otp_generator):
    """Test OTP generation."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    # Add TOTP token
    otp_generator.add_token(
        TEST_TOKENS[0]["secret"],
        TEST_TOKENS[0]["issuer"],
        TEST_TOKENS[0]["account"],
        TEST_TOKENS[0]["type"]
    )

    # Generate OTP
    otp = otp_generator.generate_otp(0)
    assert len(otp) == 6
    assert otp.isdigit()

def test_export_json(otp_generator):
    """Test JSON export."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    # Add test tokens
    for token in TEST_TOKENS:
        otp_generator.add_token(
            token["secret"],
            token["issuer"],
            token["account"],
            token["type"],
            token["counter"]
        )

    # Export to JSON
    export_data = otp_generator.export_tokens("json")
    tokens = json.loads(export_data)
    assert len(tokens) == 2
    assert tokens[0]["issuer"] == TEST_TOKENS[0]["issuer"]
    assert tokens[1]["issuer"] == TEST_TOKENS[1]["issuer"]

def test_export_google(otp_generator):
    """Test Google Authenticator export."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    # Add test tokens
    for token in TEST_TOKENS:
        otp_generator.add_token(
            token["secret"],
            token["issuer"],
            token["account"],
            token["type"],
            token["counter"]
        )

    # Export to Google format
    export_data = otp_generator.export_tokens("google")
    lines = export_data.strip().split("\n")
    assert len(lines) == 2
    assert "otpauth://" in lines[0]
    assert "otpauth://" in lines[1]

def test_import_json(otp_generator):
    """Test JSON import."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    # Create test JSON data
    json_data = json.dumps(TEST_TOKENS)

    # Import from JSON
    otp_generator.import_tokens(json_data, "json")
    tokens = otp_generator.list_tokens()
    assert len(tokens) == 2
    assert tokens[0]["issuer"] == TEST_TOKENS[0]["issuer"]
    assert tokens[1]["issuer"] == TEST_TOKENS[1]["issuer"]

def test_import_google(otp_generator):
    """Test Google Authenticator import."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    # Create test Google format data
    google_data = (
        "otpauth://totp/TestIssuer:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=TestIssuer\n"
        "otpauth://hotp/TestIssuer2:test2@example.com?secret=JBSWY3DPEHPK3PXP&issuer=TestIssuer2&counter=0"
    )

    # Import from Google format
    otp_generator.import_tokens(google_data, "google")
    tokens = otp_generator.list_tokens()
    assert len(tokens) == 2
    assert tokens[0]["issuer"] == "TestIssuer"
    assert tokens[1]["issuer"] == "TestIssuer2"

def test_backup_restore(otp_generator):
    """Test backup and restore functionality."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    # Add test tokens
    for token in TEST_TOKENS:
        otp_generator.add_token(
            token["secret"],
            token["issuer"],
            token["account"],
            token["type"],
            token["counter"]
        )

    # Create backup
    backup_file = otp_generator.create_backup(TEST_PASSWORD)
    assert Path(backup_file).exists()

    # Create new instance and restore
    with tempfile.TemporaryDirectory() as temp_dir:
        new_otp = OTPGenerator(base_dir=temp_dir)
        new_otp.restore_backup(backup_file, TEST_PASSWORD)

        # Verify restored tokens
        new_otp._initialize_encryption(TEST_PASSWORD)
        tokens = new_otp.list_tokens()
        assert len(tokens) == 2
        assert tokens[0]["issuer"] == TEST_TOKENS[0]["issuer"]
        assert tokens[1]["issuer"] == TEST_TOKENS[1]["issuer"]

def test_qr_generation(otp_generator):
    """Test QR code generation."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    # Add test token
    otp_generator.add_token(
        TEST_TOKENS[0]["secret"],
        TEST_TOKENS[0]["issuer"],
        TEST_TOKENS[0]["account"],
        TEST_TOKENS[0]["type"]
    )

    # Generate QR code to file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        otp_generator.generate_qr(0, temp_file.name)
        assert Path(temp_file.name).exists()
        assert Path(temp_file.name).stat().st_size > 0

def test_invalid_token_type(otp_generator):
    """Test invalid token type handling."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    with pytest.raises(ValueError, match="Invalid token type"):
        otp_generator.add_token(
            TEST_TOKENS[0]["secret"],
            TEST_TOKENS[0]["issuer"],
            TEST_TOKENS[0]["account"],
            "invalid_type"
        )

def test_invalid_export_format(otp_generator):
    """Test invalid export format handling."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    with pytest.raises(ValueError, match="Unsupported export format"):
        otp_generator.export_tokens("invalid_format")

def test_invalid_import_format(otp_generator):
    """Test invalid import format handling."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    with pytest.raises(ValueError, match="Unsupported import format"):
        otp_generator.import_tokens("{}", "invalid_format")

def test_invalid_token_id(otp_generator):
    """Test invalid token ID handling."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    with pytest.raises(ValueError, match="Invalid token ID"):
        otp_generator.generate_otp(999)

def test_encryption_initialization(otp_generator):
    """Test encryption initialization."""
    with pytest.raises(ValueError, match="Not initialized"):
        otp_generator.list_tokens()

def test_backup_password_required(otp_generator):
    """Test backup password requirement."""
    otp_generator.install(TEST_PASSWORD)
    otp_generator._initialize_encryption(TEST_PASSWORD)

    with pytest.raises(ValueError, match="Password required"):
        otp_generator.export_tokens("aegis")