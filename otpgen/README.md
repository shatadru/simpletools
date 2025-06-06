# OTP Generator

A command-line tool for generating 2FA (Two-Factor Authentication) codes, supporting both TOTP and HOTP tokens. This tool allows you to manage multiple 2FA accounts, generate verification codes offline, and automatically set up new accounts via QR codes.

## Features

- Generate verification codes offline
- Support for both HOTP and TOTP based tokens
- Automatic setup via QR Code
- Add multiple accounts/2FA, list, remove and generate 2FA tokens
- Cross-platform support (Linux, macOS, Windows)
- Secure keystore with password protection
- Clipboard integration for easy code copying
- Comprehensive test suite with CI integration

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### System Dependencies

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y libzbar0 zbar-tools
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install zbar
```

#### macOS
```bash
brew install zbar
```

### Python Package Installation

1. Clone the repository:
```bash
git clone https://github.com/shatadru/simpletools.git
cd simpletools/otpgen
```

2. Install the package:
```bash
pip install -r requirements.txt
```

3. Run the installation script:
```bash
python otpgen.py --install
```

## Usage

### Basic Commands

- Install/Initialize: `python otpgen.py --install`
- Add a new 2FA from QR code: `python otpgen.py --add-key <path_to_qr_image>`
- List all 2FA tokens: `python otpgen.py --list-key`
- Generate OTP: `python otpgen.py --gen-key [ID]`
- Remove a 2FA token: `python otpgen.py --remove-key [ID]`
- Clean installation: `python otpgen.py --clean-install`

### Environment Variables

- `OTPGEN_PASSWORD`: Set the keystore password (useful for automation/testing)
- `DYLD_LIBRARY_PATH`: Set the library path for macOS (e.g., `/opt/homebrew/lib`)
- `LD_LIBRARY_PATH`: Set the library path for Linux (e.g., `/usr/local/lib`)

## Development

### Running Tests

The project uses pytest for testing and tox for multi-environment testing.

1. Install test dependencies:
```bash
pip install pytest pytest-cov tox
```

2. Run tests:
```bash
# Run all tests
pytest test_otpgen.py -v

# Run tests with QR support
WITH_QR=true pytest test_otpgen.py -v

# Run tests without QR support
WITH_QR=false pytest test_otpgen.py -v -k "not test_generate_test_qr and not test_add_key and not test_gen_key and not test_remove_key"
```

3. Run tox tests (tests across multiple Python versions):
```bash
tox
```

### Continuous Integration

The project uses GitHub Actions for CI, which:
- Tests across multiple operating systems (Ubuntu, macOS, Windows)
- Tests across Python versions 3.7-3.12
- Tests with and without QR code support
- Runs tox for additional testing
- Uploads test results as artifacts

## Troubleshooting

### QR Code Scanning Issues

If you encounter issues with QR code scanning:

1. Ensure zbar is properly installed:
   - Linux: `sudo apt-get install zbar-tools` or `sudo dnf install zbar`
   - macOS: `brew install zbar`

2. Set the correct library path:
   - macOS: `export DYLD_LIBRARY_PATH=/opt/homebrew/lib`
   - Linux: `export LD_LIBRARY_PATH=/usr/local/lib`

### Password Issues

If you forget your keystore password, you'll need to:
1. Remove the existing keystore: `rm -rf ~/otpgen`
2. Run a clean installation: `python otpgen.py --clean-install`

## Security Notes

- The keystore is encrypted using AES-256-CBC with PBKDF2
- QR code images should be deleted after adding them to the keystore
- The keystore password should be strong and unique
- Never share your keystore or password

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

This project is licensed under the GPLv3 License - see the LICENSE file for details.

## Author

Shatadru Bandyopadhyay (shatadru1@gmail.com)