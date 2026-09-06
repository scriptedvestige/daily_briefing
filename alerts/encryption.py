#!/usr/bin/env python3
# This is a hacky solution for manually testing individual modules.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import argparse
from utils.file_utils import config_path, check_file, key_path
from cryptography.fernet import Fernet
import json


class Encryptor():
    """This class handles encrypting and decrypting any files that contain sensitive information.  Feed it the target file."""

    def __init__(self):
        self.key = ""
        self.key_path = key_path()
        self.target = config_path("smtp")

    def generate_key(self):
        """Create key to be used for encryption and decryption."""
        if not self.check_key():
            self.key = Fernet.generate_key()
            with open(self.key_path, "wb") as file:
                file.write(self.key)
            self.load_key()

    def check_key(self):
        """Check to see if a key exists."""
        return check_file(self.key_path)

    def load_key(self):
        """Load the key used for encryption and decryption."""
        with open(self.key_path, "rb") as file:
            self.key = file.read()

    def encrypt(self):
        """Encrypt the target file."""
        if self.check_key():
            self.load_key()
        else:
            self.generate_key()
        fernet = Fernet(self.key)
        with open(self.target, "rb") as file:
            original = file.read()
        encrypted = fernet.encrypt(original)
        with open(self.target, "wb") as file:
            file.write(encrypted)

    def decrypt(self):
        """Decrypt the target file."""
        self.load_key()
        fernet = Fernet(self.key)
        with open(self.target, "rb") as file:
            encrypted = file.read()
        original = fernet.decrypt(encrypted)
        data = json.loads(original.decode("utf-8"))
        return data

    def edit_config(self):
        """Save the decrypted file to modify config."""
        data = self.decrypt()
        with open(self.target, "w") as file:
            json.dump(data, file, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encrypt or decrypt the smtp config for editing.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--encrypt", action="store_true", help="Encrypt the target config file.")
    group.add_argument("--decrypt", action="store_true", help="Decrypt the target config file to edit it.")
    args = parser.parse_args()

    enc = Encryptor()
    if args.encrypt:
        enc.encrypt()
    elif args.decrypt:
        enc.edit_config()
