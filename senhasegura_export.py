

"""
senhasegura API - Exportador de Credenciais
Passo 1: autenticacao OAuth2
"""

from dotenv import load_dotenv
load_dotenv()
import os
import sys
import requests
import time
from dataclasses import dataclass, asdict
import csv

BASE_URL      = os.getenv("SENHASEGURA_URL")
CLIENT_ID     = os.getenv("SENHASEGURA_ID")
CLIENT_SECRET = os.getenv("SENHASEGURA_SECRET")
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() != "false"
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.3"))
OUTPUT_CSV    = os.getenv("OUTPUT_CSV", "credentials_export.csv")

@dataclass
class Credential:
    id: str = ""
    identifier: str = ""
    username: str = ""
    hostname: str = ""
    ip: str = ""
    port: str = ""
    domain: str = ""
    model: str = ""
    password: str = ""
    expiration_time: str = ""
    additional: str = ""
    error: str = ""


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


def get_credential_detail(token: str, cred_id: str) -> dict:
    url = f"{BASE_URL}/api/pam/credential/{cred_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30, verify=VERIFY_SSL)
    resp.raise_for_status()
    return resp.json().get("credential", {})



def export_to_csv(credentials: list, path: str) -> None:
    fieldnames = list(asdict(Credential()).keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for cred in credentials:
            writer.writerow(asdict(cred))
    print(f"CSV salvo em: {path} ({len(credentials)} linha(s))")





if __name__ == "__main__":
    token = get_access_token()
    print(f"Token obtido: {token[:20]}...")
    raw_list = list_credentials(token)
    print(f"{len(raw_list)} credencial(is) encontrada(s).")
    
    results = []
    for idx, item in enumerate(raw_list, start=1):
        cred_id = str(item.get("id", ""))
        print(f"[{idx}/{len(raw_list)}] Buscando id={cred_id} ...")
        detail = get_credential_detail(token, cred_id)
        results.append(Credential(
            id=cred_id,
            identifier=item.get("identifier", ""),
            username=item.get("username", ""),
            hostname=item.get("hostname", ""),
            ip=item.get("management_ip", ""),
            password=detail.get("password", ""),
            port=detail.get("port", ""),
            domain=detail.get("domain", ""),
            model=detail.get("model", ""),
            expiration_time=detail.get("expiration_time", ""),
            additional=detail.get("additional", ""),
        ))
        time.sleep(REQUEST_DELAY)

    export_to_csv(results, OUTPUT_CSV)
