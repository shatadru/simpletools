#!/usr/bin/env python3
"""
Author: Shatadru Bandyopadhyay
Email: shatadru1@gmail.com
License: GPLv3

OTP Generator - 2 Factor Authentication for Linux
Python conversion of the original bash script

Features:
- Generate verification code offline
- Support for both HOTP and TOTP based tokens
- Automatic setup via QR Code
- Add multiple accounts/2FA, list, remove and generate 2FA tokens
- Encrypted storage of secrets
"""

import argparse
import os
import sys
import json
import base64
import hashlib
import getpass
import subprocess
import tempfile
import shutil
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import platform
import xml.etree.ElementTree as ET
import zipfile
import re
import logging
from datetime import datetime

# Third-party imports (will be checked and installed if needed)
try:
    import pyotp
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from PIL import Image
    import pyperclip
    import requests
    import qrcode
except ImportError as e:
    print(f"Required package not found: {e}")
    print("Please install required packages:")
    print("pip install pyotp cryptography pillow pyperclip requests qrcode")
    sys.exit(1)

# Try to import pyzbar, but don't fail if not available
try:
    from pyzbar import pyzbar
    ZBAR_AVAILABLE = True
except ImportError:
    ZBAR_AVAILABLE = False
    print("Warning: pyzbar not available. QR code scanning will not work.")
    print("Please install pyzbar: pip install pyzbar")

VERSION = "0.8.0-python"

print('DEBUG: sys.executable:', sys.executable)
print('DEBUG: sys.path:', sys.path)

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[96m'

class Logger:
    """Logger class to handle different debug levels"""

    def __init__(self, debug_level: int = 2):
        self.debug_level = debug_level

    def fatal_error(self, message: str):
        """Print fatal error and exit"""
        if self.debug_level >= 1:
            print(f"{Colors.RED}{Colors.BOLD}Fatal Error{Colors.RESET}: {message}")
        sys.exit(255)

    def info(self, message: str):
        """Print info message"""
        if self.debug_level >= 3:
            print(f"{Colors.BLUE}{Colors.BOLD}Info{Colors.RESET}: {message}")

    def warning(self, message: str):
        """Print warning message"""
        if self.debug_level >= 2:
            print(f"{Colors.YELLOW}{Colors.BOLD}Warning{Colors.RESET}: {message}")

    def success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}{Colors.BOLD}Success{Colors.RESET}: {message}")

    def question(self, message: str):
        """Print question message"""
        print(f"{Colors.CYAN}{Colors.BOLD}Question{Colors.RESET}: {message}")

class OTPGenerator:
    """Main OTP Generator class with enhanced features."""

    VERSION = "1.0.0"
    SUPPORTED_APPS = ["freeotp", "google", "microsoft", "aegis"]

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize OTP Generator with base directory."""
        self.base_dir = Path(base_dir or os.path.expanduser("~/otpgen"))
        self.keystore_file = self.base_dir / ".secret_list"
        self.backup_dir = self.base_dir / "backups"
        self._ensure_directories()
        self._fernet = None

    def _ensure_directories(self) -> None:
        """Ensure required directories exist with proper permissions."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.base_dir.chmod(0o700)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.chmod(0o700)

    def _get_encryption_key(self, password: str) -> bytes:
        """Generate encryption key from password."""
        salt = b'otpgen_salt'  # In production, store this securely
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _initialize_encryption(self, password: str) -> None:
        """Initialize encryption with password."""
        key = self._get_encryption_key(password)
        self._fernet = Fernet(key)

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet."""
        if not self._fernet:
            raise ValueError("Encryption not initialized")
        return self._fernet.encrypt(data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet."""
        if not self._fernet:
            raise ValueError("Encryption not initialized")
        return self._fernet.decrypt(encrypted_data.encode()).decode()

    def install(self, password: str) -> None:
        """Install OTP Generator with initial password."""
        if self.keystore_file.exists():
            raise ValueError("OTP Generator already installed")

        self._initialize_encryption(password)
        self._encrypt_data("[]")  # Initialize empty keystore
        logger.info("Installation successful")

    def add_token(self, secret: str, issuer: str, account: str,
                 token_type: str = "totp", counter: int = 0) -> None:
        """Add a new token to the keystore."""
        if not self._fernet:
            raise ValueError("Not initialized. Please install first.")

        # Validate token type
        if token_type not in ["totp", "hotp"]:
            raise ValueError("Invalid token type. Must be 'totp' or 'hotp'")

        # Read existing tokens
        tokens = json.loads(self._decrypt_data(self.keystore_file.read_text()))

        # Check for duplicates
        for token in tokens:
            if (token["issuer"] == issuer and
                token["account"] == account and
                token["secret"] == secret):
                raise ValueError("Token already exists")

        # Add new token
        tokens.append({
            "secret": secret,
            "issuer": issuer,
            "account": account,
            "type": token_type,
            "counter": counter
        })

        # Save encrypted tokens
        self.keystore_file.write_text(self._encrypt_data(json.dumps(tokens)))
        logger.info(f"Added token for {issuer} - {account}")

    def list_tokens(self) -> List[Dict]:
        """List all tokens in the keystore."""
        if not self._fernet:
            raise ValueError("Not initialized. Please install first.")

        return json.loads(self._decrypt_data(self.keystore_file.read_text()))

    def generate_otp(self, token_id: int) -> str:
        """Generate OTP for a specific token."""
        if not self._fernet:
            raise ValueError("Not initialized. Please install first.")

        tokens = json.loads(self._decrypt_data(self.keystore_file.read_text()))
        if not 0 <= token_id < len(tokens):
            raise ValueError(f"Invalid token ID: {token_id}")

        token = tokens[token_id]
        if token["type"] == "totp":
            totp = pyotp.TOTP(token["secret"])
            return totp.now()
        else:  # HOTP
            hotp = pyotp.HOTP(token["secret"])
            otp = hotp.at(token["counter"])
            # Increment counter
            token["counter"] += 1
            self.keystore_file.write_text(self._encrypt_data(json.dumps(tokens)))
            return otp

    def export_tokens(self, format: str = "json", password: Optional[str] = None) -> str:
        """Export tokens in various formats."""
        if format not in ["json", "freeotp", "google", "microsoft", "aegis"]:
            raise ValueError(f"Unsupported export format: {format}")

        tokens = self.list_tokens()

        if format == "json":
            return json.dumps(tokens, indent=2)

        elif format == "freeotp":
            # FreeOTP uses a custom XML format
            root = ET.Element("tokens")
            for token in tokens:
                token_elem = ET.SubElement(root, "token")
                ET.SubElement(token_elem, "secret").text = token["secret"]
                ET.SubElement(token_elem, "issuer").text = token["issuer"]
                ET.SubElement(token_elem, "account").text = token["account"]
                ET.SubElement(token_elem, "type").text = token["type"]
                ET.SubElement(token_elem, "counter").text = str(token["counter"])
            return ET.tostring(root, encoding='unicode')

        elif format == "google":
            # Google Authenticator uses a custom URI format
            uris = []
            for token in tokens:
                uri = f"otpauth://{token['type']}/{token['issuer']}:{token['account']}?"
                uri += f"secret={token['secret']}&issuer={token['issuer']}"
                if token["type"] == "hotp":
                    uri += f"&counter={token['counter']}"
                uris.append(uri)
            return "\n".join(uris)

        elif format == "microsoft":
            # Microsoft Authenticator uses a custom JSON format
            ms_tokens = []
            for token in tokens:
                ms_token = {
                    "secretKey": token["secret"],
                    "issuer": token["issuer"],
                    "name": token["account"],
                    "type": token["type"].upper(),
                    "counter": token["counter"] if token["type"] == "hotp" else 0
                }
                ms_tokens.append(ms_token)
            return json.dumps(ms_tokens, indent=2)

        elif format == "aegis":
            # Aegis uses a custom JSON format with encryption
            if not password:
                raise ValueError("Password required for Aegis export")

            aegis_data = {
                "version": 1,
                "header": {
                    "slots": None,
                    "params": None
                },
                "db": {
                    "version": 1,
                    "entries": []
                }
            }

            for token in tokens:
                entry = {
                    "type": token["type"].upper(),
                    "name": token["account"],
                    "issuer": token["issuer"],
                    "secret": token["secret"],
                    "counter": token["counter"] if token["type"] == "hotp" else 0
                }
                aegis_data["db"]["entries"].append(entry)

            return json.dumps(aegis_data, indent=2)

    def import_tokens(self, data: str, format: str, password: Optional[str] = None) -> None:
        """Import tokens from various formats."""
        if format not in ["json", "freeotp", "google", "microsoft", "aegis"]:
            raise ValueError(f"Unsupported import format: {format}")

        if format == "json":
            tokens = json.loads(data)
            for token in tokens:
                self.add_token(
                    secret=token["secret"],
                    issuer=token["issuer"],
                    account=token["account"],
                    token_type=token["type"],
                    counter=token.get("counter", 0)
                )

        elif format == "freeotp":
            root = ET.fromstring(data)
            for token_elem in root.findall("token"):
                self.add_token(
                    secret=token_elem.find("secret").text,
                    issuer=token_elem.find("issuer").text,
                    account=token_elem.find("account").text,
                    token_type=token_elem.find("type").text,
                    counter=int(token_elem.find("counter").text)
                )

        elif format == "google":
            for line in data.strip().split("\n"):
                match = re.match(r"otpauth://(totp|hotp)/([^:]+):([^?]+)\?(.+)", line)
                if match:
                    token_type, issuer, account, params = match.groups()
                    secret = re.search(r"secret=([^&]+)", params).group(1)
                    counter = int(re.search(r"counter=(\d+)", params).group(1)) if "counter=" in params else 0
                    self.add_token(secret, issuer, account, token_type, counter)

        elif format == "microsoft":
            tokens = json.loads(data)
            for token in tokens:
                self.add_token(
                    secret=token["secretKey"],
                    issuer=token["issuer"],
                    account=token["name"],
                    token_type=token["type"].lower(),
                    counter=token.get("counter", 0)
                )

        elif format == "aegis":
            if not password:
                raise ValueError("Password required for Aegis import")

            data = json.loads(data)
            for entry in data["db"]["entries"]:
                self.add_token(
                    secret=entry["secret"],
                    issuer=entry["issuer"],
                    account=entry["name"],
                    token_type=entry["type"].lower(),
                    counter=entry.get("counter", 0)
                )

    def create_backup(self, password: str) -> str:
        """Create an encrypted backup of the keystore."""
        if not self._fernet:
            raise ValueError("Not initialized. Please install first.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_{timestamp}.enc"

        # Create backup with additional metadata
        backup_data = {
            "version": self.VERSION,
            "timestamp": timestamp,
            "tokens": json.loads(self._decrypt_data(self.keystore_file.read_text()))
        }

        # Encrypt and save backup
        backup_file.write_text(self._encrypt_data(json.dumps(backup_data)))
        logger.info(f"Created backup: {backup_file}")
        return str(backup_file)

    def restore_backup(self, backup_file: str, password: str) -> None:
        """Restore from an encrypted backup."""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise ValueError(f"Backup file not found: {backup_file}")

        # Initialize encryption with backup password
        self._initialize_encryption(password)

        # Read and decrypt backup
        backup_data = json.loads(self._decrypt_data(backup_path.read_text()))

        # Verify backup version
        if backup_data["version"] != self.VERSION:
            logger.warning(f"Backup version {backup_data['version']} differs from current version {self.VERSION}")

        # Restore tokens
        self.keystore_file.write_text(self._encrypt_data(json.dumps(backup_data["tokens"])))
        logger.info(f"Restored backup from {backup_file}")

    def generate_qr(self, token_id: int, output_file: Optional[str] = None) -> None:
        """Generate QR code for a token."""
        tokens = self.list_tokens()
        if not 0 <= token_id < len(tokens):
            raise ValueError(f"Invalid token ID: {token_id}")

        token = tokens[token_id]
        uri = f"otpauth://{token['type']}/{token['issuer']}:{token['account']}?"
        uri += f"secret={token['secret']}&issuer={token['issuer']}"
        if token["type"] == "hotp":
            uri += f"&counter={token['counter']}"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        if output_file:
            img.save(output_file)
        else:
            # Display QR code in terminal if possible
            try:
                img.show()
            except Exception:
                logger.warning("Could not display QR code. Please specify an output file.")

def print_help():
    """Print help message"""
    help_text = f"""
otpgen.py: 2 Factor Authentication for Linux

This tool allows you to generate 2 step verification codes in Linux command line

Features:
* Generate verification code offline
* Support for both HOTP and TOTP based tokens
* Automatic setup via QR Code
* Add multiple accounts/2FA, list, remove and generate 2FA tokens
* Encrypted storage of secrets

Usage: python3 otpgen.py [OPTIONS]

Options:
  -V, --version              Print version
  -i, --install              Install otpgen
  --clean-install            Clean any local data and re-install
  -a, --add-token SECRET ISSUER ACCOUNT TYPE
                             Add a new token (TYPE: totp or hotp)
  -l, --list-tokens          List all tokens
  -g, --generate ID          Generate OTP for token ID
  -e, --export FORMAT        Export tokens in specified format
  -I, --import FORMAT FILE   Import tokens from specified format
  -b, --backup               Create backup
  -r, --restore FILE         Restore from backup file
  -q, --qr ID                Generate QR code for token ID
  -d, --debug LEVEL          Set debug level (0-4, default: 2)
  -s, --silent               Same as "--debug 0"
  -h, --help                 Show this help message

Debug Levels:
  4: Debug    3: Info    2: Warning (Default)    1: Error    0: Silent

Author: Shatadru Bandyopadhyay (shatadru1@gmail.com)
License: GPLv3
Link: https://github.com/shatadru/simpletools
"""
    print(help_text)

def main():
    """Main entry point for the OTP Generator."""
    parser = argparse.ArgumentParser(description="OTP Generator - A secure command-line tool for managing 2FA tokens")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--install", action="store_true", help="Install OTP Generator")
    parser.add_argument("--clean-install", action="store_true", help="Clean any local data and re-install")
    parser.add_argument("--add-token", nargs=4, metavar=("SECRET", "ISSUER", "ACCOUNT", "TYPE"),
                       help="Add a new token (TYPE: totp or hotp)")
    parser.add_argument("--list-tokens", action="store_true", help="List all tokens")
    parser.add_argument("--generate", type=int, metavar="ID", help="Generate OTP for token ID")
    parser.add_argument("--export", choices=OTPGenerator.SUPPORTED_APPS + ["json"],
                       help="Export tokens in specified format")
    parser.add_argument("--import", dest="import_format", choices=OTPGenerator.SUPPORTED_APPS + ["json"],
                       help="Import tokens from specified format")
    parser.add_argument("--import-file", help="File to import tokens from")
    parser.add_argument("--backup", action="store_true", help="Create backup")
    parser.add_argument("--restore", help="Restore from backup file")
    parser.add_argument("--qr", type=int, metavar="ID", help="Generate QR code for token ID")
    parser.add_argument("--qr-file", help="Output file for QR code")
    parser.add_argument("-d", "--debug", type=int, choices=[0, 1, 2, 3, 4], default=2,
                      help="Debug level (0: Silent, 1: Error, 2: Warning, 3: Info, 4: Debug)")
    parser.add_argument("-s", "--silent", action="store_true", help="Same as --debug 0")

    args = parser.parse_args()

    try:
        otp = OTPGenerator()

        if args.version:
            print(f"OTP Generator version {OTPGenerator.VERSION}")
            return

        if args.install:
            password = getpass.getpass("Enter password for keystore: ")
            otp.install(password)
            return

        if args.clean_install:
            if otp.base_dir.exists():
                shutil.rmtree(otp.base_dir)
            otp.install(password)
            return

        if args.add_token:
            secret, issuer, account, token_type = args.add_token
            password = getpass.getpass("Enter keystore password: ")
            otp._initialize_encryption(password)
            otp.add_token(secret, issuer, account, token_type)
            return

        if args.list_tokens:
            password = getpass.getpass("Enter keystore password: ")
            otp._initialize_encryption(password)
            tokens = otp.list_tokens()
            for i, token in enumerate(tokens):
                print(f"{i}: {token['issuer']} - {token['account']} ({token['type']})")
            return

        if args.generate is not None:
            password = getpass.getpass("Enter keystore password: ")
            otp._initialize_encryption(password)
            otp_code = otp.generate_otp(args.generate)
            print(f"OTP: {otp_code}")
            return

        if args.export:
            password = getpass.getpass("Enter keystore password: ")
            otp._initialize_encryption(password)
            export_data = otp.export_tokens(args.export, password)
            print(export_data)
            return

        if args.import_format:
            if not args.import_file:
                print("Error: --import-file required for import")
                return
            password = getpass.getpass("Enter keystore password: ")
            otp._initialize_encryption(password)
            with open(args.import_file) as f:
                import_data = f.read()
            otp.import_tokens(import_data, args.import_format, password)
            return

        if args.backup:
            password = getpass.getpass("Enter keystore password: ")
            otp._initialize_encryption(password)
            backup_file = otp.create_backup(password)
            print(f"Backup created: {backup_file}")
            return

        if args.restore:
            password = getpass.getpass("Enter backup password: ")
            otp.restore_backup(args.restore, password)
            return

        if args.qr is not None:
            password = getpass.getpass("Enter keystore password: ")
            otp._initialize_encryption(password)
            otp.generate_qr(args.qr, args.qr_file)
            return

        parser.print_help()

    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()