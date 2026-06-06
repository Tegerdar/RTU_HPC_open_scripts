#!/usr/bin/env python3
import os
import sys
import argparse
from dotenv import load_dotenv
from ldap3 import Server, Connection, ALL, SUBTREE

def parse_arguments():
    """
    Standardizes the CLI interface for automation and pipeline integration.
    Arguments map directly to specific LDAP/MAM filtering strategies.
    """
    parser = argparse.ArgumentParser(description="Extended LDAP and MAM search tool (LDAP as primary source).")
    
    parser.add_argument('-o', '--output', required=False, help="Save results to a file (optional)")
    parser.add_argument('-n', '--no-format', action='store_true', help="Output in CSV format")
    parser.add_argument('-a', '--all', action='store_true', help="Also show MAM 'ghosts' (users in MAM but missing in LDAP)")
    
    parser.add_argument('-O', '--org', help="Filter STRICTLY by LDAP Organization (o attribute)")
    parser.add_argument('-m', '--mam', help="Filter STRICTLY by MAM accounts")
    parser.add_argument('-B', '--both-org-mam', help="Filter by EITHER LDAP Organization OR MAM accounts (Combined)")
    
    parser.add_argument('-U', '--uid', help="Filter by username (UID)")
    parser.add_argument('-C', '--cn', help="Filter by name and surname (LDAP CN)")
    parser.add_argument('-M', '--mail', help="Filter by email address (LDAP MAIL)")
    
    return parser.parse_args()

def main():
    load_dotenv()
    
    ldap_password = os.getenv("LDAP_PASSWORD")
    ldap_base_dn = os.getenv("LDAP_BASE_DN")
    ldap_bind_dn = os.getenv("LDAP_BIND_DN")
    ldap_uri = os.getenv("LDAP_URI")

    # Fail-fast constraint: ensure the script halts immediately before executing any network logic if the environment is misconfigured.
    if not ldap_password or not ldap_base_dn or not ldap_bind_dn:
        print("Error: Missing LDAP configuration in .env file.", file=sys.stderr)
        sys.exit(1)

    args = parse_arguments()

if __name__ == "__main__":
    main()
