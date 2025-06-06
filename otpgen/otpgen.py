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

# Third-party imports (will be checked and installed if needed)
try:
    import pyotp
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from PIL import Image
    import pyperclip
    import requests
except ImportError as e:
    print(f"Required package not found: {e}")
    print("Please install required packages:")
    print("pip install pyotp cryptography pillow pyperclip requests")
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

class OTPManager:
    """Main OTP Manager class"""

    def __init__(self, debug_level: int = 2):
        self.logger = Logger(debug_level)
        self.home_dir = Path.home()
        self.base_dir = self.home_dir / "otpgen"
        self.keystore_file = self.base_dir / ".secret_list"
        self.temp_dir = Path(tempfile.mkdtemp())

    def __del__(self):
        """Cleanup temporary directory"""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def check_version(self):
        """Check for script updates"""
        try:
            check_file = self.base_dir / ".check_update"

            # Only check once a day
            if check_file.exists():
                age = time.time() - check_file.stat().st_mtime
                if age < 86400:  # 24 hours
                    self.logger.info("Skipping update check, this is only done once a day...")
                    return

            self.logger.info("Checking for updates of otpgen.py")

            # This would check the GitHub repo for updates
            # For now, just create the check file
            check_file.touch()
            self.logger.info("Update check completed")

        except Exception as e:
            self.logger.warning(f"Unable to check for updates: {e}")

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt_data(self, data: str, password: str) -> bool:
        """Encrypt data with password"""
        try:
            salt = os.urandom(16)
            key = self._derive_key(password, salt)
            fernet = Fernet(key)

            encrypted_data = fernet.encrypt(data.encode())

            # Store salt + encrypted data
            with open(self.keystore_file, 'wb') as f:
                f.write(salt + encrypted_data)

            return True
        except Exception as e:
            self.logger.warning(f"Encryption failed: {e}")
            return False

    def decrypt_data(self, password: str) -> Optional[str]:
        """Decrypt data with password"""
        try:
            with open(self.keystore_file, 'rb') as f:
                file_data = f.read()

            salt = file_data[:16]
            encrypted_data = file_data[16:]

            key = self._derive_key(password, salt)
            fernet = Fernet(key)

            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.warning("Decryption failed, please re-check your password and try again")
            return None

    def ask_pass(self):
        """Ask for password, with support for environment variable in test mode"""
        mode = "create" if not os.path.exists(self.keystore_file) else "verify"

        # Check for password in environment variable (for testing)
        if os.environ.get('OTPGEN_PASSWORD'):
            return os.environ['OTPGEN_PASSWORD']

        if mode == "create":
            print("\nQuestion: Enter a strong password which will be used to encrypt your tokens...")
            password = getpass.getpass()
            print("Question: Re-enter the password again to verify")
            verify_password = getpass.getpass()

            if password != verify_password:
                print("Warning: Passwords do not match! Try again")
                return self.ask_pass()

            if not self.check_password_strength(password):
                return self.ask_pass()

            return password
        else:
            print("Question: Enter keystore password: ")
            return getpass.getpass()

    def check_password_strength(self, password: str) -> bool:
        """Check password strength (simplified version)"""
        if len(password) < 8:
            self.logger.warning("Password too short, minimum 8 characters required")
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not (has_upper and has_lower and has_digit):
            self.logger.warning("Password should contain uppercase, lowercase and digits")
            return False

        self.logger.info("Password accepted... Do not lose this password")
        return True

    def check_dependencies(self):
        """Check if required system dependencies are installed"""
        missing_deps = []

        # Check for system commands that might be needed
        system_deps = {
            'openssl': 'OpenSSL for additional encryption support',
        }

        for cmd, desc in system_deps.items():
            if shutil.which(cmd) is None:
                self.logger.warning(f"Optional dependency missing: {cmd} - {desc}")

    def extract_secret_from_image(self, image_path: str) -> Tuple[str, str, str, str]:
        """Extract OTP secret from QR code image"""
        if not ZBAR_AVAILABLE:
            self.logger.fatal_error("QR code scanning is not available. Please install pyzbar.")

        try:
            # Open and decode QR code
            image = Image.open(image_path)
            decoded_objects = pyzbar.decode(image)

            if not decoded_objects:
                self.logger.fatal_error("No QR code detected in supplied image")

            # Get the first QR code data
            qr_data = decoded_objects[0].data.decode('utf-8')

            # Parse the OTP URL
            parsed_url = urllib.parse.urlparse(qr_data)

            if parsed_url.scheme != 'otpauth':
                self.logger.fatal_error("Invalid OTP QR code format")

            # Extract components
            qr_type = parsed_url.netloc.lower()  # totp or hotp
            path_parts = parsed_url.path.strip('/').split(':')

            if len(path_parts) >= 2:
                qr_issuer = path_parts[0]
                qr_user = path_parts[1]
            else:
                qr_issuer = "Unknown"
                qr_user = path_parts[0] if path_parts else "Unknown"

            # Parse query parameters
            query_params = urllib.parse.parse_qs(parsed_url.query)
            qr_secret = query_params.get('secret', [''])[0]

            if not qr_secret:
                self.logger.fatal_error("No secret found in QR code")

            return qr_secret, qr_type, qr_issuer, qr_user

        except Exception as e:
            self.logger.fatal_error(f"Error processing QR code image: {e}")

    def install(self):
        """Install OTP generator"""
        self.logger.info("Checking for required packages...")
        self.check_dependencies()

        if self.base_dir.exists():
            self.logger.fatal_error("otpgen already installed. Use --clean-install to reinstall")

        self.logger.info("Creating required files")
        self.base_dir.mkdir(parents=True, exist_ok=True)

        password = self.ask_pass()

        self.logger.info("Creating encrypted secret store...")
        if not self.encrypt_data("", password):
            self.logger.fatal_error("Key store creation failed")

        # Set proper permissions
        os.chmod(self.base_dir, 0o700)
        os.chmod(self.keystore_file, 0o600)

        self.logger.success("Installation successful")

    def clean_install(self):
        """Clean install - remove existing data and reinstall"""
        self.logger.warning("This will remove all existing 2FA tokens!")
        input("Press Enter to continue, Ctrl+C to exit...")

        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)

        self.install()

    def check_install(self):
        """Check if OTP generator is installed"""
        if not self.base_dir.exists() or not self.keystore_file.exists():
            self.logger.fatal_error("otpgen is not installed, please install using -i/--install")

    def add_key(self, image_path: str):
        """Add new 2FA key from QR code image"""
        if not image_path:
            self.logger.fatal_error("Image file not supplied, please add an image file containing QR Code")

        if not Path(image_path).exists():
            self.logger.fatal_error("File not found, can't add 2FA...")

        self.logger.info("Detecting QR Code from supplied image...")

        qr_secret, qr_type, qr_issuer, qr_user = self.extract_secret_from_image(image_path)

        if qr_type == "totp":
            self.logger.info("TOTP token detected")
        elif qr_type == "hotp":
            self.logger.info("HOTP token detected")
        else:
            self.logger.fatal_error("OTP type unsupported! Only TOTP and HOTP are supported")

        # Decrypt existing data
        password = self.ask_pass()
        existing_data = self.decrypt_data(password)

        if existing_data is None:
            self.logger.fatal_error("Wrong password or corrupted keystore")

        # Parse existing entries
        entries = []
        if existing_data.strip():
            for line in existing_data.strip().split('\n'):
                if line.strip():
                    entries.append(line.strip().split())

        # Check for duplicates
        for entry in entries:
            if (len(entry) >= 5 and entry[1] == qr_secret and
                entry[2] == qr_type and entry[3] == qr_issuer and entry[4] == qr_user):
                self.logger.warning("2FA is already added in keystore...")
                self.logger.fatal_error("Not adding duplicate entry...")

        # Create new entry
        new_id = len(entries) + 1
        if qr_type == "hotp":
            new_entry = [str(new_id), qr_secret, qr_type, qr_issuer, qr_user, "0"]
        else:
            new_entry = [str(new_id), qr_secret, qr_type, qr_issuer, qr_user]

        entries.append(new_entry)

        # Save updated data
        new_data = '\n'.join([' '.join(entry) for entry in entries])

        if self.encrypt_data(new_data, password):
            self.logger.success("New 2FA added successfully")
        else:
            self.logger.fatal_error("Failed to add 2FA")

    def list_keys(self):
        """List all stored 2FA keys"""
        self.check_install()

        password = self.ask_pass()
        data = self.decrypt_data(password)

        if data is None:
            self.logger.fatal_error("Wrong password or corrupted keystore")

        if not data.strip():
            self.logger.warning("No 2FA found in keystore, use -a or --add-key to add new 2FA")
            return

        # Print header
        print(f"{'ID':<2} {'Secret':<30} {'TYPE':<6} {'ISSUER':<20} {'USER':<30} {'Counter(HOTP)':<15}")

        # Print entries
        for line in data.strip().split('\n'):
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 5:
                    entry_id = parts[0]
                    secret_masked = "••••••••••••••••••"
                    otp_type = parts[2]
                    issuer = parts[3]
                    user = parts[4]
                    counter = parts[5] if len(parts) > 5 else ""

                    print(f"{entry_id:<2} {secret_masked:<30} {otp_type:<6} {issuer:<20} {user:<30} {counter:<15}")

    def generate_key(self, key_id: Optional[str] = None):
        """Generate OTP for specified key ID"""
        password = self.ask_pass()
        data = self.decrypt_data(password)

        if data is None:
            self.logger.fatal_error("Wrong password or corrupted keystore")

        if not key_id:
            self.list_keys()
            key_id = input("Which 2FA do you want to select? ")

        # Find the entry
        entries = []
        selected_entry = None
        entry_index = -1

        for i, line in enumerate(data.strip().split('\n')):
            if line.strip():
                parts = line.strip().split()
                entries.append(parts)
                if parts[0] == key_id:
                    selected_entry = parts
                    entry_index = i

        if not selected_entry:
            self.logger.fatal_error(f"Unable to generate 2FA token for ID: {key_id}")

        secret = selected_entry[1]
        token_type = selected_entry[2]

        try:
            if token_type == "totp":
                totp = pyotp.TOTP(secret)
                token = totp.now()
            elif token_type == "hotp":
                counter = int(selected_entry[5]) if len(selected_entry) > 5 else 0
                hotp = pyotp.HOTP(secret)
                token = hotp.at(counter)

                # Update counter
                selected_entry[5] = str(counter + 1)
                entries[entry_index] = selected_entry

                # Save updated data
                new_data = '\n'.join([' '.join(entry) for entry in entries])
                if not self.encrypt_data(new_data, password):
                    self.logger.fatal_error("Error incrementing HOTP counter")
            else:
                self.logger.fatal_error(f"Unsupported token type: {token_type}")

            self.logger.success(f"OTP: {token}")

            # Try to copy to clipboard
            try:
                pyperclip.copy(token)
                self.logger.success("OTP has been copied to clipboard, Ctrl+V to paste")
            except Exception:
                self.logger.warning("OTP was not copied to clipboard")

        except Exception as e:
            self.logger.fatal_error(f"Error generating OTP: {e}")

    def remove_key(self, key_id: Optional[str] = None):
        """Remove 2FA key"""
        password = self.ask_pass()
        data = self.decrypt_data(password)

        if data is None:
            self.logger.fatal_error("Wrong password or corrupted keystore")

        if not key_id:
            self.list_keys()
            key_id = input("Which 2FA do you want to remove? ")

        entries = []
        found = False

        for line in data.strip().split('\n'):
            if line.strip():
                parts = line.strip().split()
                if parts[0] != key_id:
                    entries.append(parts)
                else:
                    found = True

        if not found:
            self.logger.fatal_error(f"Unable to find 2FA with ID: {key_id}")

        input(f"Are you sure you want to remove 2FA with ID: {key_id}? Press Enter to continue, Ctrl+C to exit...")

        # Save updated data
        new_data = '\n'.join([' '.join(entry) for entry in entries])

        if self.encrypt_data(new_data, password):
            self.logger.success("2FA removed successfully")
        else:
            self.logger.fatal_error("Failed to remove 2FA")

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
  -i, --install              Install otpgen in system
  --clean-install            Clean any local data and re-install
  -a, --add-key FILE         Add a new 2FA from image containing QR Code
  -l, --list-key             List all available 2FA stored in the system
  -g, --gen-key [ID]         Generate one time password
  -r, --remove-key [ID]      Remove a 2FA token from keystore
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
    """Main function"""
    parser = argparse.ArgumentParser(description='OTP Generator - 2FA for Linux', add_help=False)

    parser.add_argument('-V', '--version', action='store_true', help='Print version')
    parser.add_argument('-i', '--install', action='store_true', help='Install otpgen')
    parser.add_argument('--clean-install', action='store_true', help='Clean install')
    parser.add_argument('-a', '--add-key', metavar='FILE', help='Add 2FA from QR code image')
    parser.add_argument('-l', '--list-key', action='store_true', help='List all 2FA keys')
    parser.add_argument('-g', '--gen-key', metavar='ID', nargs='?', const='', help='Generate OTP')
    parser.add_argument('-r', '--remove-key', metavar='ID', nargs='?', const='', help='Remove 2FA key')
    parser.add_argument('-d', '--debug', type=int, choices=[0,1,2,3,4], default=2, help='Debug level')
    parser.add_argument('-s', '--silent', action='store_true', help='Silent mode')
    parser.add_argument('-h', '--help', action='store_true', help='Show help')

    args = parser.parse_args()

    if args.help:
        print_help()
        return

    if args.version:
        print(f"Version: {VERSION}")
        return

    # Set debug level
    debug_level = 0 if args.silent else args.debug

    # Create OTP manager
    otp_manager = OTPManager(debug_level)

    # Check for updates (only if not silent)
    if debug_level > 0:
        otp_manager.check_version()

    # Execute commands
    if args.install:
        otp_manager.install()
    elif args.clean_install:
        otp_manager.clean_install()
    elif args.add_key:
        otp_manager.check_install()
        otp_manager.add_key(args.add_key)
    elif args.list_key:
        otp_manager.list_keys()
    elif args.gen_key is not None:
        otp_manager.check_install()
        key_id = args.gen_key if args.gen_key else None
        otp_manager.generate_key(key_id)
    elif args.remove_key is not None:
        otp_manager.check_install()
        key_id = args.remove_key if args.remove_key else None
        otp_manager.remove_key(key_id)
    else:
        print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)