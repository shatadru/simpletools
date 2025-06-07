#!/usr/bin/env python3
"""
Setup script for OTP Generator Python version
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from setuptools import setup, find_packages

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def install_system_dependencies():
    """Install system dependencies based on the distribution"""
    print("Checking system dependencies...")

    # Check for zbar (needed for QR code scanning)
    if shutil.which('zbarimg') is None:
        print("Installing zbar for QR code scanning...")

        # Detect package manager
        if shutil.which('apt-get'):
            subprocess.run(['sudo', 'apt-get', 'update'], check=False)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'libzbar0'], check=False)
        elif shutil.which('yum'):
            subprocess.run(['sudo', 'yum', 'install', '-y', 'zbar'], check=False)
        elif shutil.which('dnf'):
            subprocess.run(['sudo', 'dnf', 'install', '-y', 'zbar'], check=False)
        elif shutil.which('pacman'):
            subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'zbar'], check=False)
        else:
            print("Warning: Could not detect package manager. Please install zbar manually.")
    else:
        print("✓ zbar is already installed")

def install_python_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")

    requirements_file = Path(__file__).parent / "requirements.txt"

    if requirements_file.exists():
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], check=True)
            print("✓ Python dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("Error: Failed to install Python dependencies")
            print("You can install them manually with:")
            print(f"pip install -r {requirements_file}")
            sys.exit(1)
    else:
        print("Warning: requirements.txt not found")

def make_executable():
    """Make the Python script executable"""
    script_path = Path(__file__).parent / "otpgen.py"
    if script_path.exists():
        os.chmod(script_path, 0o755)
        print("✓ Made otpgen.py executable")

def create_symlink():
    """Create a symlink in user's local bin directory"""
    script_path = Path(__file__).parent / "otpgen.py"
    local_bin = Path.home() / ".local" / "bin"

    if not local_bin.exists():
        local_bin.mkdir(parents=True)

    symlink_path = local_bin / "otpgen"

    try:
        if symlink_path.exists():
            symlink_path.unlink()

        symlink_path.symlink_to(script_path.resolve())
        print(f"✓ Created symlink at {symlink_path}")

        # Check if ~/.local/bin is in PATH
        path_env = os.environ.get('PATH', '')
        if str(local_bin) not in path_env:
            print(f"Note: Add {local_bin} to your PATH to use 'otpgen' command")
            print(f"Add this line to your ~/.bashrc or ~/.zshrc:")
            print(f"export PATH=\"$PATH:{local_bin}\"")

    except Exception as e:
        print(f"Warning: Could not create symlink: {e}")

def main():
    """Main setup function"""
    print("Setting up OTP Generator (Python version)...")
    print("=" * 50)

    check_python_version()
    install_system_dependencies()
    install_python_dependencies()
    make_executable()
    create_symlink()

    print("=" * 50)
    print("✓ Setup completed successfully!")
    print("\nYou can now use the OTP generator with:")
    print("  python3 otpgen.py --help")
    print("  or")
    print("  otpgen --help (if symlink was created successfully)")
    print("\nTo install the OTP generator itself, run:")
    print("  python3 otpgen.py --install")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)

setup(
    name="otpgen",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyotp>=2.6.0",
        "cryptography>=3.4.8",
        "pillow>=8.3.2",
        "pyzbar>=0.1.8",
        "pyperclip>=1.8.2",
        "requests>=2.25.1",
        "qrcode>=7.4.2",
        "pypng",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "otpgen=otpgen.otpgen:main",
        ],
    },
)