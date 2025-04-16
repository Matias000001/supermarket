"""
This module handles the creation and retrieval of the secret key used for
secure session management and cryptographic operations. It also provides
instructions for configuring the secret key in the server's environment.
"""

import os


SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key")

# Set the secret key as an environment variable on the server ~/.bashrc to file
# echo "export SECRET_KEY="39e5b8dd1de7afdc786df2b0cdf7a8f1"" >> ~/.bashrc
# source ~/.bashrc
