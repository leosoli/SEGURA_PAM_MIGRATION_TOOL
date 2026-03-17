"""
senhasegura - Migrador de Senhas entre Vaults
Passo 2: leitura do CSV de origem
"""

import os
import csv
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()

DEST_URL    = os.getenv("DEST_URL")
DEST_ID     = os.getenv("DEST_ID")
DEST_SECRET = os.getenv("DEST_SECRET")
INPUT_CSV   = os.getenv("INPUT_CSV", "credentials_export.csv")
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


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    token = get_access_token(DEST_URL, DEST_ID, DEST_SECRET)
    rows = load_csv(INPUT_CSV)
    print(f"{len(rows)} credencial(is) carregada(s).")
    for row in rows:
        print(f"  {row.get('username')}@{row.get('hostname')}  identifier={row.get('identifier')}")