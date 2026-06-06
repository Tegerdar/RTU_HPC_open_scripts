# search/ldap_client.py
import sys
from ldap3 import Server, Connection, ALL, SUBTREE

# Import our secure configuration from the sibling file
from search.config import LDAP_URI, LDAP_BIND_DN, LDAP_PASSWORD, LDAP_BASE_DN

def fetch_all_ldap_users():
    """
    Establishes a synchronous connection to the LDAP server.
    Returns a dictionary of users keyed by UID for O(1) lookups during aggregation.
    """
    server = Server(LDAP_URI, get_info=ALL)
    ldap_master = {}
    
    try:
        # Context manager ensures connection closes automatically, even if an error occurs
        with Connection(server, user=LDAP_BIND_DN, password=LDAP_PASSWORD, auto_bind=True) as conn:
            
            # Fetch all users. We filter later in the aggregator.
            # Requesting only specific attributes minimizes network payload.
            conn.search(
                search_base=LDAP_BASE_DN,
                search_filter='(uid=*)',
                search_scope=SUBTREE,
                attributes=['dn', 'cn', 'mail', 'uid', 'o']
            )
            
            for entry in conn.entries:
                # Safely extract values, defaulting to 'N/A' if the attribute doesn't exist
                uid = entry.uid.value.lower() if 'uid' in entry else None
                
                if uid:
                    ldap_master[uid] = {
                        'uid': uid,
                        'cn': entry.cn.value if 'cn' in entry else 'N/A',
                        'mail': entry.mail.value if 'mail' in entry else 'N/A',
                        'dn': entry.entry_dn,
                        'ldap_org': entry.o.value if 'o' in entry else 'N/A'
                    }
                    
        return ldap_master
        
    except Exception as e:
        print(f"Error: Failed to fetch data from LDAP. ({e})", file=sys.stderr)
        sys.exit(1)