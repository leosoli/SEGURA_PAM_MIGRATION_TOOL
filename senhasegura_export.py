

"""
senhasegura API - Exportador de Credenciais
Passo 1: autenticacao OAuth2
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import requests

BASE_URL      = os.getenv("SENHASEGURA_URL")
CLIENT_ID     = os.getenv("SENHASEGURA_ID")
CLIENT_SECRET = os.getenv("SENHASEGURA_SECRET")
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() != "false"


def get_access_token() -> str:
    url = f"{BASE_URL}/api/oauth2/token"
    payload = {
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    resp = requests.post(url, data=payload, timeout=30, verify=VERIFY_SSL)
    resp.raise_for_status()
    return resp.json()["access_token"]

def list_credentials(token: str) -> list:
    url = f"{BASE_URL}/api/pam/credential"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30, verify=VERIFY_SSL)
    resp.raise_for_status()
    return resp.json().get("credentials", [])



if __name__ == "__main__":
    token = get_access_token()
    print(f"Token obtido: {token[:20]}...")
    credentials = list_credentials(token)
    print(f"{len(credentials)} credencial(is) encontrada(s):")
    for c in credentials:
        print(f"  id={c.get('id')}  user={c.get('username')}  host={c.get('hostname')}")

