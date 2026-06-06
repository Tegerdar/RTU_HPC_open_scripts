# config.py
import os
import sys
from dotenv import load_dotenv

# Load variables into the environment
load_dotenv()

# Export variables for other modules to import
LDAP_PASSWORD = os.getenv("LDAP_MANAGER_PASSWORD")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN")
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
LDAP_URI = os.getenv("LDAP_URI")

def validate_config():
    """
    Fails fast if the environment is missing critical secrets. 
    Prevents downstream network modules from throwing confusing connection errors.
    """
    if not all([LDAP_PASSWORD, LDAP_BASE_DN, LDAP_BIND_DN, LDAP_URI]):
        print("Error: Missing LDAP configuration in .env file.", file=sys.stderr)
        sys.exit(1)