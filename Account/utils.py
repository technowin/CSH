from django.conf import settings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import os

def get_aes_key_iv():
    key = base64.urlsafe_b64decode(settings.SECRET_KEY1.encode())  # Decode the base64 key
    key = key[:32]  # Ensure the key is exactly 32 bytes long
    iv = os.urandom(16)  # Generate a random IV
    return key, iv

def get_aes_key():
    key = base64.urlsafe_b64decode(settings.SECRET_KEY1.encode())
    return key[:32]  # Ensure the key is exactly 32 bytes long
def encrypt_email(email):
    key, iv = get_aes_key_iv()
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()

    # Padding the email to be multiples of block size
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(email.encode()) + padder.finalize()

    encrypted_email = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_email = base64.urlsafe_b64encode(iv + encrypted_email).decode()
    return encrypted_email
def base64_url_decode(input_str):
    padding = 4 - (len(input_str) % 4)
    if padding:
        input_str += "=" * padding
    return base64.urlsafe_b64decode(input_str.encode())

def decrypt_email(encrypted_email):
    encrypted_email_bytes = base64_url_decode(encrypted_email)
    iv = encrypted_email_bytes[:16]
    cipher_text = encrypted_email_bytes[16:]
    key = get_aes_key()
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()

    decrypted_padded_email = decryptor.update(cipher_text) + decryptor.finalize()

    # Unpad the decrypted email
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    email = unpadder.update(decrypted_padded_email) + unpadder.finalize()
    return email.decode()

# Example usage in a Django view
