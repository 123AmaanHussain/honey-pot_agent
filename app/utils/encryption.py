"""
Encryption utilities for securing sensitive data like API tokens.
Uses Fernet symmetric encryption from the cryptography library.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

# Global Fernet instance
_fernet: Fernet = None


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key from environment.
    Falls back to a generated key if not set.
    """
    key = os.environ.get('ENCRYPTION_KEY')
    
    if key:
        # Use key from environment (should be 32 bytes, base64 encoded)
        try:
            # If it's a string, encode it
            if isinstance(key, str):
                key_bytes = key.encode('utf-8')
                # Pad or truncate to 32 bytes if needed
                if len(key_bytes) < 32:
                    key_bytes = key_bytes.ljust(32, b'\0')
                elif len(key_bytes) > 32:
                    key_bytes = key_bytes[:32]
                # Base64 encode for Fernet
                return base64.urlsafe_b64encode(key_bytes)
            return key.encode('utf-8')
        except Exception as e:
            logger.warning(f"Invalid ENCRYPTION_KEY format, generating new key: {e}")
    
    # Generate a new key if none exists or invalid
    logger.warning("No ENCRYPTION_KEY set, generating a temporary key. Set ENCRYPTION_KEY in .env for persistence.")
    return Fernet.generate_key()


def initialize_encryption():
    """Initialize the Fernet encryption instance."""
    global _fernet
    try:
        key = get_encryption_key()
        _fernet = Fernet(key)
        logger.info("Encryption initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize encryption: {e}")
        raise


def encrypt_data(data: str) -> str:
    """
    Encrypt a string value.
    
    Args:
        data: Plain text string to encrypt
        
    Returns:
        Base64 encoded encrypted string
    """
    if not _fernet:
        initialize_encryption()
    
    try:
        encrypted = _fernet.encrypt(data.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt an encrypted string.
    
    Args:
        encrypted_data: Base64 encoded encrypted string
        
    Returns:
        Decrypted plain text string
    """
    if not _fernet:
        initialize_encryption()
    
    try:
        decrypted = _fernet.decrypt(encrypted_data.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise


# Initialize on module import
try:
    initialize_encryption()
except Exception as e:
    logger.error(f"Failed to initialize encryption module: {e}")
