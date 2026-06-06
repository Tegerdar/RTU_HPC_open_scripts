# search/aggregator.py
import sys

from search.ldap_client import fetch_all_ldap_users
from search.mam_client import get_full_mam_data

def build_master_roster():
    """
    Orchestrates the data fetch and merges LDAP and MAM records into a unified structure.
    LDAP is treated as the primary source of truth for identity, while MAM enriches the data.
    """

    ldap_data = fetch_all_ldap_users()
    
    mam_data = get_full_mam_data()
    mam_users = mam_data['users']
    mam_balances = mam_data['balances']
    
    master_roster = []
    seen_uids = set()

    # If the user has no default account, or the account isn't found, it handles it gracefully.
    def get_formatted_balance(default_account):
        if not default_account or default_account == 'n/a':
            return "0.00 (No Account)"
        
        b = mam_balances.get(default_account)
        if b:
            return f"Tot: {b['total']} | Rsv: {b['reserved']} | Avl: {b['available']}"
        return "0.00 (Account Not Found)"

    # 1. Process all LDAP users and enrich with MAM data
    for uid, ldap_user in ldap_data.items():
        seen_uids.add(uid)
        
        mam_info = mam_users.get(uid)
        
        if mam_info:
            mam_orgs = " + ".join(sorted(mam_info['orgs'])) if mam_info['orgs'] else "No Account"
            status = mam_info['status']
            balance_str = get_formatted_balance(mam_info['default_account'])
        else:
            mam_orgs = "N/A"
            status = "Not in MAM"
            balance_str = "N/A"

        master_roster.append({
            'uid': uid,
            'cn': ldap_user['cn'],
            'mail': ldap_user['mail'],
            'ldap_org': ldap_user['ldap_org'],
            'mam_orgs': mam_orgs,
            'mam_status': status,
            'mam_balance': balance_str,
            'is_ghost': False # They exist in LDAP
        })

    # 2. Add MAM "Ghosts" (Users in MAM but completely missing from LDAP)
    for uid, mam_info in mam_users.items():
        if uid not in seen_uids:
            mam_orgs = " + ".join(sorted(mam_info['orgs'])) if mam_info['orgs'] else "No Account"
            balance_str = get_formatted_balance(mam_info['default_account'])
            
            master_roster.append({
                'uid': uid,
                'cn': 'N/A (MAM Ghost)',
                'mail': 'N/A',
                'ldap_org': 'N/A',
                'mam_orgs': mam_orgs,
                'mam_status': mam_info['status'],
                'mam_balance': balance_str,
                'is_ghost': True
            })

    return master_roster


def apply_filters(roster, args):
    """
    Reduces the master roster based on CLI arguments.
    Separating filtering from data ingestion makes testing and debugging much easier.
    """
    filtered_roster = []
    
    # Pre-clean filter strings so we don't have to call .lower() thousands of times in the loop
    f_cn = args.cn.lower() if args.cn else None
    f_mail = args.mail.lower() if args.mail else None
    f_org = args.org.lower() if args.org else None
    f_mam = args.mam.lower() if args.mam else None
    f_both = args.both_org_mam.lower() if args.both_org_mam else None
    f_uid = args.uid.lower().lstrip('^') if args.uid else None

    for user in roster:
        # Drop ghosts unless the --all flag is passed
        if user['is_ghost'] and not args.all:
            continue
            
        # Standard string matching
        if f_uid and f_uid not in user['uid']: continue
        if f_cn and f_cn not in user['cn'].lower(): continue
        if f_mail and f_mail not in user['mail'].lower(): continue
        
        # Organizational matching
        if f_org and f_org not in user['ldap_org'].lower(): continue
        if f_mam and f_mam not in user['mam_orgs'].lower(): continue
        
        if f_both:
            match_ldap = f_both in user['ldap_org'].lower()
            match_mam = f_both in user['mam_orgs'].lower()
            if not (match_ldap or match_mam):
                continue
                
        filtered_roster.append(user)

    return filtered_roster