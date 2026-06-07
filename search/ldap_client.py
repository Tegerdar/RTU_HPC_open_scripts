# search/ldap_client.py
import sys
from ldap3 import Server, Connection, ALL, SUBTREE

# Import our secure configuration from the sibling file
from search.config import LDAP_URI, LDAP_BIND_DN, LDAP_PASSWORD, LDAP_BASE_DN


def _first_attr_value(entry, attr_name, default='N/A'):
    """Return a safe scalar value for an LDAP attribute.

    ldap3 attributes can be scalars, lists/tuples, or missing.
    """
    if attr_name not in entry:
        return default

    value = entry[attr_name].value
    if isinstance(value, (list, tuple)):
        return value[0] if value else default
    return value if value is not None else default

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
                attributes=['cn', 'mail', 'uid', 'o']
            )
            
            for entry in conn.entries:
                # Safely extract values, defaulting to 'N/A' if the attribute doesn't exist
                uid_raw = _first_attr_value(entry, 'uid', default=None)
                uid = str(uid_raw).lower() if uid_raw is not None else None
                
                if uid:
                    ldap_master[uid] = {
                        'uid': uid,
                        'cn': _first_attr_value(entry, 'cn'),
                        'mail': _first_attr_value(entry, 'mail'),
                        'dn': entry.entry_dn,
                        'ldap_org': _first_attr_value(entry, 'o')
                    }
                    
        return ldap_master
        
    except Exception as e:
        print(f"Error: Failed to fetch data from LDAP. ({e})", file=sys.stderr)
        sys.exit(1)