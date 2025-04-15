"""
Generates a new cryptography key using Fernet and saves it to a file.
The generated key is saved in the file 'keyfile.key' in binary format.
"""

from cryptography.fernet import Fernet


key = Fernet.generate_key()
with open("keyfile.key", "wb") as key_file:
    key_file.write(key)
print("Key generated and saved!")
