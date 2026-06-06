# search/mam_client.py
import subprocess
import sys
import csv

def run_mam_csv_command(command_list):
    """
    Executes a MAM command requesting CSV output.
    Returns a list of dictionaries mapping the CSV headers to their row values.
    """
    if '--format' not in command_list:
        command_list.extend(['--format', 'csv'])
        
    try:
        result = subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        output_lines = result.stdout.decode('utf-8', errors='replace').splitlines()
        
        return list(csv.DictReader(output_lines))
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error: Failed to run {' '.join(command_list)} ({e})", file=sys.stderr)
        sys.exit(1)

def get_full_mam_data():
    """
    Retrieves Accounts, Status, and Balances from MAM using native CSV parsing.
    Returns a multi-level dictionary separating users from account balances.
    """
    mam_users = {}
    account_balances = {}

    # 1. Fetch Accounts (Organizations)
    # Headers: Name, Active, Users, Organization, Description
    account_rows = run_mam_csv_command(['mam-list-accounts'])
    for row in account_rows:
        account_name = row.get('Name', '').strip().lower()
        if not account_name: continue

        users_raw = row.get('Users', '')
        if users_raw:
            users = [u.strip().lower().lstrip('^') for u in users_raw.split(',') if u.strip()]
            for uid in users:
                if uid not in mam_users:
                    mam_users[uid] = {'orgs': set(), 'status': 'Unknown', 'default_account': 'N/A'}
                mam_users[uid]['orgs'].add(account_name)

    # 2. Fetch User Status
    # Headers: Name, Active, CommonName, PhoneNumber, EmailAddress, DefaultAccount, Description
    user_rows = run_mam_csv_command(['mam-list-users'])
    for row in user_rows:
        uid = row.get('Name', '').strip().lower().lstrip('^')
        if not uid: continue
        
        # Catch empty strings and default them to 'Unknown'
        status = row.get('Active', '').strip()
        if not status: status = 'Unknown'
        
        default_account = row.get('DefaultAccount', '').strip().lower()

        if uid in mam_users:
            mam_users[uid]['status'] = status
            mam_users[uid]['default_account'] = default_account
        else:
            mam_users[uid] = {'orgs': set(), 'status': status, 'default_account': default_account}

    # 3. Fetch Balances (Funds)
    # Headers: Id, Name, Balance, Reserved, Effective, CreditLimit, Available
    balance_rows = run_mam_csv_command(['mam-balance'])
    for row in balance_rows:
        account_name = row.get('Name', '').strip().lower()
        
        balance = row.get('Balance', '0.0000').strip()
        reserved = row.get('Reserved', '0.0000').strip()
        available = row.get('Available', '0.0000').strip()
        
        if account_name:
            account_balances[account_name] = {
                'total': balance,
                'reserved': reserved,
                'available': available
            }

    return {
        'users': mam_users,
        'balances': account_balances
    }