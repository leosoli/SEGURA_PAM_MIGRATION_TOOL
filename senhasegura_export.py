"""
senhasegura API - Exportador de Credenciais
Passo 1: autenticacao OAuth2
"""

import os
import sys
import requests

BASE_URL      = os.getenv("SENHASEGURA_URL")
CLIENT_ID     = os.getenv("SENHASEGURA_ID")
CLIENT_SECRET = os.getenv("SENHASEGURA_SECRET")


def get_access_token() -> str:
    url = f"{BASE_URL}/iso/oauth2/token"
    payload = {
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    resp = requests.post(url, data=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


if __name__ == "__main__":
    token = get_access_token()
    print(f"Token obtido: {token[:20]}...")

