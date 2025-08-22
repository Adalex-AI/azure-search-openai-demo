import os
import subprocess
import sys
from msal import ConfidentialClientApplication

def resolve_akvs(val: str) -> str:
    """
    Resolve Azure Key Vault secret URIs (akvs://) to their actual values.
    Only performs resolution if AZURE_RESOLVE_AKVS is enabled.
    """
    if not val:
        return val
    
    # Check if akvs:// resolution is enabled
    resolve_enabled = os.getenv("AZURE_RESOLVE_AKVS", "").lower() in ("1", "true", "yes")
    debug_enabled = os.getenv("AZURE_DEBUG", "").lower() in ("1", "true", "yes")
    
    if debug_enabled:
        print(f"DEBUG: resolve_akvs called with val='{val}', resolve_enabled={resolve_enabled}", file=sys.stderr)
    
    if not resolve_enabled:
        if debug_enabled:
            print("DEBUG: AZURE_RESOLVE_AKVS not enabled, returning original value", file=sys.stderr)
        return val
    
    if val.startswith("akvs://"):
        parts = val.split("/")
        # Validate akvs:// format: akvs://vault-name/secret-name
        if len(parts) < 5 or not parts[3] or not parts[4]:
            print(f"ERROR: Malformed akvs:// URI format. Expected: akvs://vault-name/secret-name", file=sys.stderr)
            return val
        
        vault = parts[3]
        name = parts[4]
        
        if debug_enabled:
            print(f"DEBUG: Attempting to resolve secret '{name}' from vault '{vault}'", file=sys.stderr)
        
        try:
            result = subprocess.run(
                ["az", "keyvault", "secret", "show", "--vault-name", vault, "--name", name, "--query", "value", "-o", "tsv"],
                capture_output=True,
                text=True,
                check=True
            )
            resolved_value = result.stdout.strip()
            if debug_enabled:
                print(f"DEBUG: Successfully resolved secret from Key Vault", file=sys.stderr)
            return resolved_value
            
        except FileNotFoundError:
            print("ERROR: Azure CLI (az) not found. Please install Azure CLI or disable AZURE_RESOLVE_AKVS.", file=sys.stderr)
            return val
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to retrieve secret from Key Vault: {e.stderr.strip() if e.stderr else str(e)}", file=sys.stderr)
            return val
    
    return val

client_id = os.getenv("AZURE_SERVER_APP_ID")
raw_secret = os.getenv("AZURE_SERVER_APP_SECRET")
tenant = os.getenv("AZURE_TENANT_ID")

# Add debugging output
debug_enabled = os.getenv("AZURE_DEBUG", "").lower() in ("1", "true", "yes")
if debug_enabled:
    print(f"DEBUG: Raw values - client_id='{client_id}', raw_secret='{raw_secret}', tenant='{tenant}'", file=sys.stderr)

client_secret = resolve_akvs(raw_secret)

if debug_enabled:
    print(f"DEBUG: After resolve_akvs - client_secret='{client_secret}'", file=sys.stderr)
    print(f"DEBUG: Final validation - client_id exists: {bool(client_id)}, client_secret exists: {bool(client_secret)}, tenant exists: {bool(tenant)}", file=sys.stderr)

if not client_id or not client_secret or not tenant:
    print({"error": "missing_env", "missing": [k for k,v in (("AZURE_SERVER_APP_ID",client_id),("AZURE_SERVER_APP_SECRET",client_secret),("AZURE_TENANT_ID",tenant)) if not v]})
else:
    authority = f"https://login.microsoftonline.com/{tenant}"
    app = ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    print(res)