from cryptography.fernet import Fernet
from django.conf import settings
import base64
def generate_key():
    return Fernet.generate_key()
def get_encryption_key():
    return settings.ENCRYPTION_KEY.encode()
def encrypt_parameter(parameter):
    cipher_suite = Fernet(get_encryption_key())
    cipher_text = cipher_suite.encrypt(parameter.encode())
    # Use base64 encoding to make the result shorter and more URL-friendly
    encoded_cipher_text = base64.urlsafe_b64encode(cipher_text).decode()
    return encoded_cipher_text

def decrypt_parameter(encoded_cipher_text):
    # Decode the base64-encoded string before decrypting
    cipher_text = base64.urlsafe_b64decode(encoded_cipher_text.encode())
    cipher_suite = Fernet(get_encryption_key())
    plain_text = cipher_suite.decrypt(cipher_text).decode()
    return plain_text
