#!/usr/bin/env python3
"""
Generate a test TOTP QR code for testing the OTP generator
"""

import pyotp
import qrcode
from pathlib import Path

def generate_test_qr():
    # Generate a random secret
    secret = pyotp.random_base32()

    # Create TOTP object
    totp = pyotp.TOTP(secret)

    # Create provisioning URI
    provisioning_uri = totp.provisioning_uri(
        name="test@example.com",
        issuer_name="Test Service"
    )

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    # Create QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Save QR code
    output_path = Path("test_qr.png")
    qr_image.save(output_path)

    print(f"Generated test QR code at: {output_path.absolute()}")
    print(f"Secret: {secret}")
    print(f"Current OTP: {totp.now()}")
    print("\nYou can use this QR code to test the OTP generator.")

if __name__ == "__main__":
    generate_test_qr()