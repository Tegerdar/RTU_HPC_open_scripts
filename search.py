#!/usr/bin/env python3
import sys
import csv
import argparse

# Import the brain of our application
from search.aggregator import build_master_roster, apply_filters

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
        print("\nNo users matched the given criteria.", file=sys.stderr)
        return

    # 1. Output to a saved CSV file
    if args.output:
        keys = roster[0].keys()
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(roster)
        print(f"\nSuccess: Saved {len(roster)} records to {args.output}", file=sys.stderr)
        return

    # 2. Output raw CSV to the terminal (Useful if you want to pipe it: python main.py -n > out.csv)
    if args.no_format:
        keys = roster[0].keys()
        writer = csv.DictWriter(sys.stdout, fieldnames=keys)
        writer.writeheader()
        writer.writerows(roster)
        return

    # 3. Pretty Terminal Output (Default)
    print(f"\nFound {len(roster)} users matching criteria:\n" + "="*50)
    for user in roster:
        # Add a visual tag if they are a ghost
        ghost_tag = "[GHOST] " if user['is_ghost'] else ""
        
        print(f"UID:      {ghost_tag}{user['uid']}")
        print(f"Name:     {user['cn']}")
        print(f"Email:    {user['mail']}")
        print(f"LDAP Org: {user['ldap_org']}")
        print(f"MAM Org:  {user['mam_orgs']}")
        print(f"Status:   {user['mam_status']}")
        print(f"Funds:    {user['mam_balance']}")
        print("-" * 50)

def main():
    # 1. Read what the user wants to do
    args = parse_arguments()
    
    try:
        # 2. Fetch all data and merge it (The Data Layer)
        master_roster = build_master_roster()
        
        # 3. Filter down the data based on arguments (The Business Logic Layer)
        filtered_roster = apply_filters(master_roster, args)
        
        # 4. Show the results (The Presentation Layer)
        output_results(filtered_roster, args)
        
    except KeyboardInterrupt:
        # Gracefully handle the user pressing Ctrl+C
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)

if __name__ == "__main__":
    main()