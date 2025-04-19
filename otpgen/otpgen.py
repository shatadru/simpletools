# otpgen.py
# Modular Python port of otpgen.sh by Shatadru Bandyopadhyay

import os
import sys
import base64
import logging
import argparse
import getpass
import pyotp
import json
import csv
from typing import List
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    import zbarlight
    from PIL import Image
except ImportError:
    zbarlight = None
    Image = None

try:
    from rich.console import Console
    from rich.logging import RichHandler

    console = Console()
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console)],
    )
    log = logging.getLogger("otpgen")

    def success(msg):
        console.print(f"[bold green]✔ {msg}")

except ImportError:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    log = logging.getLogger("otpgen")

    def success(msg):
        print(f"[SUCCESS] {msg}")


KEYSTORE_FILE = os.path.expanduser("~/.otpgen_keystore")
VERSION = "0.4-python"


class OTPGen:
    def __init__(self):
        self.password = None
        self.store = []

    def platform_check(self):
        import platform
        from shutil import which

        system = platform.system().lower()
        self._platform = system

        # macOS first — override DISPLAY logic
        if system == "darwin":
            if which("pbcopy"):
                self._platform_mode = "clipboard-available"
                return True
            else:
                log.warning("Clipboard tool 'pbcopy' missing. Run: xcode-select --install")
                self._platform_mode = "darwin"
                return "darwin"

        # Linux or other
        if os.environ.get("SSH_CONNECTION") or not os.environ.get("DISPLAY"):
            log.warning("Detected headless or SSH session. Clipboard integration may not work.")
            self._platform_mode = "headless"
            return "headless"

        if pyperclip and pyperclip.is_available():
            self._platform_mode = "clipboard-available"
            return True

        if system == "linux":
            from shutil import which
            if which("xclip") or which("xsel") or which("wl-copy"):
                self._platform_mode = "clipboard-available"
                return True
            else:
                log.warning("No clipboard utility found. Suggested: 'xclip', 'xsel', or 'wl-clipboard'.")
                self._platform_mode = "linux"
                return "linux"

        elif system == "windows":
            self._platform_mode = "clipboard-available"
            return True  # pyperclip uses ctypes for Windows clipboard

        log.warning("Unknown OS or clipboard method unsupported.")
        self._platform_mode = "unknown"
        return False

    def get_password(self, confirm=False):
        attempts = 3
        while attempts > 0:
            pw = getpass.getpass("Enter keystore password: ").strip()
            if not pw:
                log.warning("Password cannot be empty.")
                attempts -= 1
                continue
            if confirm:
                confirm_pw = getpass.getpass("Confirm password: ").strip()
                if pw != confirm_pw:
                    log.error("Passwords do not match.")
                    attempts -= 1
                    continue
            self.password = pw.encode()
            return self.password
        log.error("Maximum attempts exceeded.")
        sys.exit(1)

    def derive_key(self, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(self.password))

    def encrypt_store(self):
        if not self.password:
            self.password = self.get_password()
        salt = os.urandom(16)
        key = self.derive_key(salt)
        fernet = Fernet(key)
        token = fernet.encrypt("\n".join(self.store).encode())
        with open(KEYSTORE_FILE, "wb") as f:
            f.write(salt + token)

    def decrypt_store(self):
        if not os.path.exists(KEYSTORE_FILE):
            log.warning("Keystore file not found.")
            self.store = []
            return False

        if not self.password:
            self.get_password()

        try:
            with open(KEYSTORE_FILE, "rb") as f:
                raw = f.read()

            if len(raw) < 17:
                log.error("Keystore file is too short or corrupted.")
                return False

            salt, token = raw[:16], raw[16:]
            key = self.derive_key(salt)
            fernet = Fernet(key)
            decrypted = fernet.decrypt(token).decode()
            self.store = decrypted.strip().splitlines()
            return True

        except InvalidToken:
            log.error("Incorrect password or corrupted keystore.")
            return False

        except Exception as e:
            log.exception("Unexpected error while decrypting the keystore:")
            return False


    def install_dependencies(self):
        import platform
        import subprocess

        system = platform.system().lower()
        if system == "linux":
            req_file = "requirements-linux.txt"
        elif system == "darwin":
            req_file = "requirements-macos.txt"
        else:
            log.warning("Unsupported platform for automatic dependency install.")
            return

        if not os.path.exists(req_file):
            log.error(f"Missing {req_file} for installation.")
            return

        log.info(f"Installing dependencies from {req_file} ...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file])

    def install(self):
        if os.path.exists(KEYSTORE_FILE):
            log.warning("Keystore already exists. Use --clean-install to reset.")
            return

        self.platform_check()
        self.install_dependencies()

        self.get_password(confirm=True)
        self.encrypt_store()
        log.info("Keystore initialized successfully.")


    def clean_install(self):
        if os.path.exists(KEYSTORE_FILE):
            os.remove(KEYSTORE_FILE)
            log.info("Existing keystore removed.")
        self.install()

    def add_key(self, source):
        if os.path.isfile(source):
            self.platform_check()
            if self._platform == "darwin":
                try:
                    from pyzbar.pyzbar import decode
                    from PIL import Image
                except ImportError:
                    log.error("Missing pyzbar or Pillow for QR parsing on macOS.")
                    return
                img = Image.open(source)
                decoded = decode(img)
                if not decoded:
                    log.error("No QR code found in image.")
                    return
                data = decoded[0].data.decode("utf-8")
            elif zbarlight and Image:
                with open(source, "rb") as img_file:
                    image = Image.open(img_file)
                    image.load()
                    codes = zbarlight.scan_codes("qrcode", image)
                    if not codes:
                        log.error("No QR code found in image.")
                        return
                    data = codes[0].decode("utf-8")
            else:
                log.error("QR decoding requires zbarlight or pyzbar + Pillow.")
                return

            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(data)
            label = parsed.path.strip("/")
            otp_type = parsed.netloc
            params = parse_qs(parsed.query)
            secret = params.get("secret", [""])[0]
            issuer = params.get("issuer", [""])[0]
            if not all([secret, otp_type, label]):
                log.error("Incomplete data in QR code.")
                return
        else:
            log.error("Manual secret input not supported in this mode.")
            return

        self.get_password()
        self.decrypt_store()
        counter = "0"
        new_id = str(len(self.store) + 1)
        entry = f"{new_id} {secret} {otp_type} {issuer} {label} {counter}"
        self.store.append(entry)
        self.encrypt_store()
        success("2FA entry added from QR code.")


    def list_keys(self):
        self.get_password()
        self.decrypt_store()
        if not self.store:
            log.info("No keys found in the keystore.")
            return
        print("ID  TYPE  ISSUER          LABEL")
        for line in self.store:
            parts = line.strip().split()
            if len(parts) >= 5:
                print(f"{parts[0]:<3} {parts[2]:<5} {parts[3]:<15} {parts[4]}")

    def generate_token(self, key_id, no_clip=False):
        self.get_password()
        self.decrypt_store()
        for i, line in enumerate(self.store):
            parts = line.strip().split()
            if parts and parts[0] == key_id:
                if len(parts) < 5:
                    log.error("Malformed keystore entry. Missing required fields.")
                    return None

                secret = parts[1]
                otp_type = parts[2]
                token = None

                try:
                    if otp_type == "totp":
                        token = pyotp.TOTP(secret).now()
                    elif otp_type == "hotp":
                        if len(parts) < 6:
                            log.error("Missing HOTP counter.")
                            return None
                        counter = int(parts[5])
                        token = pyotp.HOTP(secret).at(counter)
                        parts[5] = str(counter + 1)
                        self.store[i] = " ".join(parts)
                        self.encrypt_store()
                    else:
                        log.error("Unsupported OTP type.")
                        return None

                    success(f"OTP: {token}")
                    if pyperclip and not no_clip:
                        platform_result = self.platform_check()
                        try:
                            pyperclip.copy(token)
                            success("OTP copied to clipboard.")
                        except pyperclip.PyperclipException:
                            if platform_result == "headless":
                                log.warning("Clipboard unavailable in headless/SSH mode. Use --no-clip.")
                            elif platform_result == "linux":
                                log.warning("Clipboard copy failed. Try installing 'xclip', 'xsel', or 'wl-clipboard'.")
                            elif platform_result == "darwin":
                                log.warning("Clipboard copy failed. On macOS, run: xcode-select --install")
                            else:
                                log.warning("Clipboard copy failed. Consider using --no-clip or configuring system clipboard.")
                    return token
                except Exception as e:
                    log.error(f"OTP generation failed: {e}")
                    return None
        log.error("Invalid ID. Key not found.")
        return None

    def remove_key(self, key_id):
        self.get_password()
        self.decrypt_store()
        new_store = [line for line in self.store if not line.startswith(f"{key_id} ")]
        if len(new_store) == len(self.store):
            log.error("ID not found. Nothing removed.")
        else:
            self.store = new_store
            self.encrypt_store()
            success(f"2FA entry {key_id} removed.")

    def export_keys(self, fmt, path=None):
        self.get_password()
        self.decrypt_store()

        if not self.store:
            log.warning("No data to export.")
            return

        if not path:
            path = f"otpgen_export.{fmt}"

        if fmt == "json":
            out = []
            for line in self.store:
                parts = line.strip().split()
                entry = {
                    "id": parts[0],
                    "secret": parts[1],
                    "type": parts[2],
                    "issuer": parts[3],
                    "label": parts[4],
                    "counter": parts[5] if len(parts) > 5 else ""
                }
                out.append(entry)
            with open(path, "w") as f:
                json.dump(out, f, indent=2)
            success(f"Exported to {path}")

        elif fmt == "csv":
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "secret", "type", "issuer", "label", "counter"])
                for line in self.store:
                    parts = line.strip().split()
                    row = parts + [""] * (6 - len(parts))  # pad to ensure 6 fields
                    writer.writerow(row)
            success(f"Exported to {path}")
        else:
            log.error("Unsupported export format.")


    def import_keys(self, path, fmt):
        self.get_password()
        self.decrypt_store()
        new_entries = []
        if fmt == "json":
            with open(path) as f:
                items = json.load(f)
                for item in items:
                    new_id = str(len(self.store) + len(new_entries) + 1)
                    new_entries.append(
                        f"{new_id} {item['secret']} {item['type']} {item['issuer']} {item['label']} {item['counter']}"
                    )
        elif fmt == "csv":
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    new_id = str(len(self.store) + len(new_entries) + 1)
                    new_entries.append(
                        f"{new_id} {row['secret']} {row['type']} {row['issuer']} {row['label']} {row['counter']}"
                    )
        self.store.extend(new_entries)
        self.encrypt_store()
        success(f"Imported {len(new_entries)} keys from {path}.")

    def generate_qr(self, key_id, out_file=None):
        import urllib.parse

        if not qrcode:
            log.error("QR generation requires the 'qrcode' module. Try: pip install qrcode[pil]")
            return

        self.get_password()
        self.decrypt_store()

        for line in self.store:
            parts = line.strip().split()
            if parts and parts[0] == key_id and len(parts) >= 5:
                secret, otp_type, issuer, label = parts[1], parts[2], parts[3], parts[4]
                uri = f"otpauth://{otp_type}/{urllib.parse.quote(label)}?secret={secret}&issuer={urllib.parse.quote(issuer)}"
                img = qrcode.make(uri)

                if not out_file:
                    out_file = f"otpgen_{issuer}_{label}.png".replace(" ", "_")
                img.save(out_file)
                success(f"QR code saved to {out_file}")

                if getattr(self, '_platform_mode', '') == "headless":
                    log.info("Skipping auto-open: headless environment detected.")
                else:
                    try:
                        import webbrowser
                        webbrowser.open(out_file)
                        log.info("QR code opened in image viewer/browser.")
                    except Exception as e:
                        log.warning(f"QR code saved but could not auto-open: {e}")
                return

        log.error("Key not found or missing fields for QR generation.")

def main():
    parser = argparse.ArgumentParser(description="otpgen (Python CLI Edition)")
    parser.add_argument("-i", "--install", action="store_true")
    parser.add_argument("--clean-install", action="store_true")
    parser.add_argument("-a", "--add-key", type=str)
    parser.add_argument("-l", "--list-key", action="store_true")
    parser.add_argument("-g", "--gen-key", type=str, nargs="?", const=None)
    parser.add_argument(
        "--no-clip", action="store_true", help="Do not copy OTP to clipboard"
    )
    parser.add_argument("-r", "--remove-key", type=str)
    parser.add_argument("--export", type=str, choices=["json", "csv"])
    parser.add_argument("--import", dest="import_file", type=str)
    parser.add_argument("--import-format", type=str, choices=["json", "csv"])
    parser.add_argument("--qr", type=str, help="Generate QR code for ID")
    parser.add_argument("-V", "--version", action="store_true")

    args = parser.parse_args()
    app = OTPGen()
    app.platform_check()

    try:
        if args.install:
            app.install()
        elif args.clean_install:
            app.clean_install()
        elif args.add_key:
            app.add_key(args.add_key)
        elif args.list_key:
            app.list_keys()
        elif args.gen_key is not None:
            app.generate_token(args.gen_key, no_clip=args.no_clip)
        elif args.remove_key:
            app.remove_key(args.remove_key)
        elif args.export:
            app.export_keys(args.export)
        elif args.import_file and args.import_format:
            app.import_keys(args.import_file, args.import_format)
        elif args.qr:
            app.generate_qr(args.qr)
        elif args.version:
            print("otpgen version:", VERSION)
        else:
            parser.print_help()
    except IndexError as e:
        log.error("Malformed entry in keystore. Please check stored data.")
        sys.exit(1)
    except Exception as e:
        log.exception("An unexpected error occurred:")
        sys.exit(1)


if __name__ == "__main__":
    main()

