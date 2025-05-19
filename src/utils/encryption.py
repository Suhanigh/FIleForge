"""
File encryption utilities for the File System Explorer.
"""

import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
from typing import Tuple

class Encryption:
    """Class handling file encryption and decryption."""
    
    @staticmethod
    def generate_key(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Generate an encryption key from a password.
        
        Args:
            password: The password to use for key generation
            salt: Optional salt for key generation
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt_file(file_path: str, password: str) -> Tuple[bool, str]:
        """
        Encrypt a file using a password.
        
        Args:
            file_path: Path to the file to encrypt
            password: Password to use for encryption
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Generate key
            key, salt = Encryption.generate_key(password)
            f = Fernet(key)
            
            # Read file
            with open(file_path, 'rb') as file:
                data = file.read()
            
            # Encrypt data
            encrypted_data = f.encrypt(data)
            
            # Save encrypted file
            encrypted_path = file_path + '.encrypted'
            with open(encrypted_path, 'wb') as file:
                # Save salt and encrypted data
                metadata = {
                    'salt': base64.b64encode(salt).decode(),
                    'original_name': os.path.basename(file_path)
                }
                file.write(json.dumps(metadata).encode() + b'\n')
                file.write(encrypted_data)
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def decrypt_file(file_path: str, password: str) -> Tuple[bool, str]:
        """
        Decrypt a file using a password.
        
        Args:
            file_path: Path to the encrypted file
            password: Password to use for decryption
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Read encrypted file
            with open(file_path, 'rb') as file:
                # Read metadata
                metadata_line = file.readline()
                metadata = json.loads(metadata_line)
                salt = base64.b64decode(metadata['salt'])
                original_name = metadata['original_name']
                
                # Read encrypted data
                encrypted_data = file.read()
            
            # Generate key
            key, _ = Encryption.generate_key(password, salt)
            f = Fernet(key)
            
            # Decrypt data
            decrypted_data = f.decrypt(encrypted_data)
            
            # Save decrypted file
            decrypted_path = os.path.join(
                os.path.dirname(file_path),
                original_name
            )
            with open(decrypted_path, 'wb') as file:
                file.write(decrypted_data)
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def is_encrypted_file(file_path: str) -> bool:
        """
        Check if a file is encrypted.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is encrypted, False otherwise
        """
        try:
            with open(file_path, 'rb') as file:
                # Try to read metadata
                metadata_line = file.readline()
                metadata = json.loads(metadata_line)
                return 'salt' in metadata and 'original_name' in metadata
        except:
            return False 