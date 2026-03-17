"""
senhasegura - Migrador de Senhas entre Vaults
Passo 4: encontrar credencial no destino por username + hostname + ip
"""

import os
import csv
import time
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()

DEST_URL      = os.getenv("DEST_URL")
DEST_ID       = os.getenv("DEST_ID")
DEST_SECRET   = os.getenv("DEST_SECRET")
INPUT_CSV     = os.getenv("INPUT_CSV", "credentials_export.csv")
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.3"))
VERIFY_SSL    = os.getenv("VERIFY_SSL", "true").lower() != "false"

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


def list_dest_credentials(token):
    url = f"{DEST_URL}/api/pam/credential"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()
    return resp.json().get("credentials", [])


def find_credential(dest_creds, username, hostname, ip):
    for cred in dest_creds:
        same_user = cred.get("username",       "").strip().lower() == username.strip().lower()
        same_host = cred.get("hostname",       "").strip().lower() == hostname.strip().lower()
        same_ip   = cred.get("management_ip",  "").strip()         == ip.strip()
        if same_user and (same_host or same_ip):
            return str(cred.get("id"))
    return None


if __name__ == "__main__":
    token = get_access_token(DEST_URL, DEST_ID, DEST_SECRET)
    rows = load_csv(INPUT_CSV)
    dest_creds = list_dest_credentials(token)

    print(f"{len(rows)} credencial(is) no CSV / {len(dest_creds)} no destino.")

    for row in rows:
        username = row.get("username", "")
        hostname = row.get("hostname", "")
        ip       = row.get("ip",       "")
        cred_id  = find_credential(dest_creds, username, hostname, ip)
        if cred_id:
            print(f"  MATCH id={cred_id}  {username}@{hostname}")
        else:
            print(f"  NO MATCH  {username}@{hostname} ({ip})")