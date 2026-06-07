#!/usr/bin/env python3
import sys
import csv
import io
import argparse

# Import the brain of our application
from search.aggregator import build_master_roster, apply_filters


def configure_stdio():
    """Use UTF-8 output when possible and avoid locale-related crashes."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass


def _safe_text(value, stream):
    """Coerce text so writing to ASCII terminals never raises UnicodeEncodeError."""
    encoding = getattr(stream, 'encoding', None) or 'utf-8'
    return str(value).encode(encoding, errors='replace').decode(encoding, errors='replace')


def safe_print(text, stream=sys.stdout, end='\n'):
    print(_safe_text(text, stream), file=stream, end=end)

def parse_arguments():
    """
    Standardizes the CLI interface.
    """
    parser = argparse.ArgumentParser(description="Ultimate HPC User Admin Tool (LDAP + MAM)")
    
    # Output flags
    parser.add_argument('-o', '--output', required=False, help="Save results to a CSV file")
    parser.add_argument('-n', '--no-format', action='store_true', help="Output in raw CSV format to terminal (useful for piping)")
    parser.add_argument('-a', '--all', action='store_true', help="Show MAM 'ghosts' (users in MAM but missing in LDAP)")
    
    # Organization filters
    parser.add_argument('-O', '--org', help="Filter STRICTLY by LDAP Organization")
    parser.add_argument('-m', '--mam', help="Filter STRICTLY by MAM accounts")
    parser.add_argument('-B', '--both-org-mam', help="Filter by EITHER LDAP Organization OR MAM accounts")
    
    # User filters
    parser.add_argument('-U', '--uid', help="Filter by username (UID)")
    parser.add_argument('-C', '--cn', help="Filter by name and surname (LDAP CN)")
    parser.add_argument('-M', '--mail', help="Filter by email address")
    
    return parser.parse_args()

def output_results(roster, args):
    """
    The Presentation Layer. Routes the filtered data to the terminal or a file.
    """
    if not roster:
        safe_print("\nNo users matched the given criteria.", stream=sys.stderr)
        return

    # 1. Output to a saved CSV file
    if args.output:
        keys = roster[0].keys()
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(roster)
        safe_print(f"\nSuccess: Saved {len(roster)} records to {args.output}", stream=sys.stderr)
        return

    # 2. Output raw CSV to the terminal (Useful if you want to pipe it: python main.py -n > out.csv)
    if args.no_format:
        keys = roster[0].keys()
        # Write CSV in memory first, then emit via Unicode-safe terminal writer.
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=keys)
        writer.writeheader()
        writer.writerows(roster)
        safe_print(buffer.getvalue(), end='')
        return

    # 3. Pretty Terminal Output (Default)
    safe_print(f"\nFound {len(roster)} users matching criteria:\n" + "="*50)
    for user in roster:
        # Add a visual tag if they are a ghost
        ghost_tag = "[GHOST] " if user['is_ghost'] else ""
        
        safe_print(f"UID:      {ghost_tag}{user['uid']}")
        safe_print(f"Name:     {user['cn']}")
        safe_print(f"Email:    {user['mail']}")
        safe_print(f"LDAP Org: {user['ldap_org']}")
        safe_print(f"MAM Org:  {user['mam_orgs']}")
        safe_print(f"Status:   {user['mam_status']}")
        safe_print(f"Funds:    {user['mam_balance']}")
        safe_print("-" * 50)

def main():
    configure_stdio()

    args = parse_arguments()
    
    try:
        # Fetch all data and merge it
        master_roster = build_master_roster()
        
        filtered_roster = apply_filters(master_roster, args)
        
        output_results(filtered_roster, args)
        
    except KeyboardInterrupt:
        # Gracefully handle the user pressing Ctrl+C
        safe_print("\nOperation cancelled by user.", stream=sys.stderr)
        sys.exit(130)

if __name__ == "__main__":
    main()