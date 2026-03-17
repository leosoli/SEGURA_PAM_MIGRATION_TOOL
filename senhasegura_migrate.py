"""
senhasegura - Migrador de Senhas entre Vaults
Passo 7: salvar relatorio de migracao em CSV
"""

import os
import csv
import time
import requests
import urllib3
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

DEST_URL      = os.getenv("DEST_URL")
DEST_ID       = os.getenv("DEST_ID")
DEST_SECRET   = os.getenv("DEST_SECRET")
INPUT_CSV     = os.getenv("INPUT_CSV",  "credentials_export.csv")
REPORT_CSV    = os.getenv("REPORT_CSV", "migration_report.csv")
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.3"))
VERIFY_SSL    = os.getenv("VERIFY_SSL", "true").lower() != "false"


if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class MigrationResult:
    username:   str = ""
    hostname:   str = ""
    ip:         str = ""
    dest_id:    str = ""
    identifier: str = ""
    status:     str = ""   # success | skipped | error
    detail:     str = ""




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
    """
    Returns {"id": ..., "identifier": ...} of the first match,
    or None. Matches by username + hostname or management_ip.
    """
    for cred in dest_creds:
        same_user = cred.get("username",      "").strip().lower() == username.strip().lower()
        same_host = cred.get("hostname",      "").strip().lower() == hostname.strip().lower()
        same_ip   = cred.get("management_ip", "").strip()         == ip.strip()
        if same_user and (same_host or same_ip):
            return {
                "id":         str(cred.get("id")),
                "identifier": cred.get("identifier", ""),
            }
    return None



def update_password(token, match, username, hostname, ip, password):
    url = f"{DEST_URL}/api/pam/credential"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }
    body = {
        "identifier": match["identifier"],
        "username":   username,
        "hostname":   hostname,
        "ip":         ip,
        "content":    password,
    }
    resp = requests.post(url, json=body, headers=headers, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()


def save_report(results, path):
    fieldnames = list(asdict(MigrationResult()).keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    print(f"Relatorio salvo em: {path}")


if __name__ == "__main__":
    token      = get_access_token(DEST_URL, DEST_ID, DEST_SECRET)
    rows       = load_csv(INPUT_CSV)
    dest_creds = list_dest_credentials(token)
    print(f"{len(rows)} credencial(is) no CSV / {len(dest_creds)} no destino.")

    results = []

    for idx, row in enumerate(rows, start=1):
        username = row.get("username", "").strip()
        hostname = row.get("hostname", "").strip()
        ip       = row.get("ip",       "").strip()
        password = row.get("password", "").strip()

        print(f"[{idx}/{len(rows)}] {username}@{hostname} ...")
        result = MigrationResult(username=username, hostname=hostname, ip=ip)

        if not password:
            result.status = "skipped"
            result.detail = "password vazia no CSV"
            print("  SKIP — password vazia no CSV")
            results.append(result)
            continue

        match = find_credential(dest_creds, username, hostname, ip)
        if not match:
            result.status = "skipped"
            result.detail = "sem correspondencia no destino"
            print("  SKIP — sem correspondencia no destino")
            results.append(result)
            continue

        update_password(token, match, username, hostname, ip, password)
        result.dest_id    = match["id"]
        result.identifier = match["identifier"]
        result.status     = "success"
        print(f"  OK — id={match['id']}  identifier={match['identifier']}")
        results.append(result)
        time.sleep(REQUEST_DELAY)

    save_report(results, REPORT_CSV)