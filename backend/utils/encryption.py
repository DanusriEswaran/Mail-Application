import os
from cryptography.fernet import Fernet
from config import KEY_FILE

class Encryption:
    _instance = None
    _cipher = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Encryption, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Generate key if it doesn't exist
        if not os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'wb') as f:
                f.write(Fernet.generate_key())
        
        # Load the key
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
        
        self._cipher = Fernet(key)
    
    def encrypt(self, data):
        """Encrypt data (string) and return encrypted string"""
        if isinstance(data, str):
            data = data.encode()
        return self._cipher.encrypt(data).decode()
    
    def decrypt(self, data):
        """Decrypt data (string) and return decrypted string"""
        if isinstance(data, str):
            data = data.encode()
        try:
            return self._cipher.decrypt(data).decode()
        except Exception:
            return "[Failed to decrypt]"