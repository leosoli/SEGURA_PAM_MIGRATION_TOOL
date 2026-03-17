"""
senhasegura - Migrador de Senhas entre Vaults
Passo 1: autenticacao no vault de destino
"""

import os
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()

DEST_URL    = os.getenv("DEST_URL")
DEST_ID     = os.getenv("DEST_ID")
DEST_SECRET = os.getenv("DEST_SECRET")
VERIFY_SSL  = os.getenv("VERIFY_SSL", "true").lower() != "false"

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_access_token(base_url, client_id, client_secret):
    url = f"{base_url}/api/oauth2/token"
    payload = {
        "grant_type":    "client_credentials",
        "client_id":     client_id,
        "client_secret": client_secret,
    }
    resp = requests.post(url, data=payload, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


if __name__ == "__main__":
    token = get_access_token(DEST_URL, DEST_ID, DEST_SECRET)
    print(f"Token obtido: {token[:20]}...")