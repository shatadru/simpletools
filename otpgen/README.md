# OTPGen - 2 Factor Authentication for Linux

A command-line tool for generating 2FA codes on Linux systems. This tool allows you to generate verification codes offline and supports both HOTP and TOTP based tokens.

## Features

* Generate verification code offline
* Support for both HOTP and TOTP based tokens
* Add multiple accounts/2FA, list, remove and generate 2FA tokens
* Supports: Fedora, Ubuntu, Debian, RHEL (more to be added including CentOS, Manjaro, Mint)

## Installation

### Prerequisites

The following packages are required:

```bash
# For Fedora/RHEL:
sudo dnf install oathtool openssl xclip zbar cracklib

# For Ubuntu/Debian:
sudo apt-get install oathtool openssl xclip zbar-tools libcrack2
```

### Installing OTPGen

1. Clone the repository:
```bash
git clone https://github.com/shatadru/simpletools.git
cd simpletools/otpgen
```

2. Install OTPGen:
```bash
./otpgen.sh --install
```

## Usage

```bash
# Install OTPGen
./otpgen.sh --install

# Add a new 2FA from QR code image
./otpgen.sh --add-key <path-to-qr-image>

# List all available 2FA tokens
./otpgen.sh --list-key

# Generate OTP for a specific token
./otpgen.sh --gen-key [ID]

# Remove a 2FA token
./otpgen.sh --remove-key [ID]

# Clean install (removes all existing tokens)
./otpgen.sh --clean-install
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest
```

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## Author

* **Shatadru Bandyopadhyay** - [shatadru1@gmail.com](mailto:shatadru1@gmail.com)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request