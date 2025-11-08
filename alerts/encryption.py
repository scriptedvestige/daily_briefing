#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.file_utils import config_path, check_file
from cryptography.fernet import Fernet
import json


class Encryptor():
    """This class handles encrypting and decrypting any files that contain sensitive information.  Feed it the target file."""

    def __init__(self):
        self.key = ""
        self.key_path = f"\\key\path" # UPDATE THIS PATH TO WHERE YOUR KEY LIVES
        self.target = config_path("smtp")

    def generate_key(self):
        """Create key to be used for encryption and decryption."""
        # If key does not already exist, make a key.
        if not self.check_key:
            self.key = Fernet.generate_key()
            with open(self.key_path, "wb") as file:
                file.write(self.key)
            # Load the freshly made key.
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
        # Check to see if a key exists.  If yes, load the key, if not, make and load the key.
        if self.check_key():
            self.load_key()
        else:
            self.generate_key()
        # Create encryption object, load the original data, encrypt it, overwrite the file with the encrypted data.
        fernet = Fernet(self.key)
        with open(self.target, "rb") as file:
            original = file.read()
        encrypted = Fernet.encrypt(self=fernet, data=original)
        with open(self.target, "wb") as file:
            file.write(encrypted)

    def decrypt(self):
        """Decrypt the target file."""
        self.load_key()
        # Create encryption object, load the encrypted data, decrypt it, overwrite the file with the decrypted data.
        fernet = Fernet(self.key)
        with open(self.target, "rb") as file:
            encrypted = file.read()
        original = Fernet.decrypt(self=fernet, token=encrypted)
        data = json.loads(original.decode("utf-8"))
        return data
    
    def save_config(self):
        """Save the decrypted file to modify config."""
        data = self.decrypt()
        with open(self.target, "w") as file:
            json.dump(data, file, indent=4)


if __name__ == "__main__":
    enc = Encryptor()
    enc.encrypt()
    # enc.save_config()
