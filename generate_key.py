from cryptography.fernet import Fernet

# Luo uusi avain
key = Fernet.generate_key()

# Tallenna avain tiedostoon
with open("keyfile.key", "wb") as key_file:
    key_file.write(key)

print("Key generated and saved!")