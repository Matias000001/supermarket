"""
This module handles the creation and retrieval of the secret key used for
secure session management and cryptographic operations. It also provides
instructions for configuring the secret key in the server's environment.
"""

import os


SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key")

# Set the secret key as an environment variable on the server ~/.bashrc to file
# echo "export SECRET_KEY="xxxxxxxxx" >> ~/.bashrc
# source ~/.bashrc
