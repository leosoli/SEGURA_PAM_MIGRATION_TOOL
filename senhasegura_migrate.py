"""
senhasegura - Migrador de Senhas entre Vaults
=============================================
Le o CSV gerado pelo senhasegura_export.py, busca cada credencial
no vault de destino por username + hostname/ip, e atualiza a senha
via POST /api/pam/credential usando identifier e o campo content.

Pre-requisitos:
  pip install -r requirements.txt

Configuracao:
  Preencha o .env com as variaveis do vault de destino.
"""

import os
import sys
import csv
import time
import logging
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# CONFIG — lido do arquivo .env
# ──────────────────────────────────────────────
DEST_URL      = os.getenv("DEST_URL")
DEST_ID       = os.getenv("DEST_ID")
DEST_SECRET   = os.getenv("DEST_SECRET")
INPUT_CSV     = os.getenv("INPUT_CSV",  "credentials_export.csv")
REPORT_CSV    = os.getenv("REPORT_CSV", "migration_report.csv")
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.3"))
VERIFY_SSL    = os.getenv("VERIFY_SSL", "true").lower() != "false"
# ──────────────────────────────────────────────

# Desabilita flags de warning por uso de certificado SSL não confiado
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)



@dataclass
class MigrationResult:
    username:   str = ""
    hostname:   str = ""
    ip:         str = ""
    dest_id:    str = ""
    identifier: str = ""
    status:     str = ""   # success | skipped | error
    detail:     str = ""


def build_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = build_session()


def get_access_token(base_url, client_id, client_secret):
    url = f"{base_url}/api/oauth2/token"
    payload = {
        "grant_type":    "client_credentials",
        "client_id":     client_id,
        "client_secret": client_secret,
    }
    log.info("Autenticando em %s ...", url)
    try:
        resp = SESSION.post(url, data=payload, verify=VERIFY_SSL, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.SSLError:
        log.error("Erro SSL. Defina VERIFY_SSL=false para certificados auto-assinados.")
        sys.exit(1)
    except requests.exceptions.ConnectionError as exc:
        log.error("Nao foi possivel conectar em %s: %s", base_url, exc)
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        log.error("Falha na autenticacao HTTP %s: %s", resp.status_code, resp.text)
        sys.exit(1)

    token = resp.json().get("access_token")
    if not token:
        log.error("Resposta de token inesperada: %s", resp.text)
        sys.exit(1)

    log.info("Token obtido com sucesso.")
    return token


def load_csv(path):
    if not os.path.exists(path):
        log.error("Arquivo CSV nao encontrado: %s", path)
        sys.exit(1)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def list_dest_credentials(token):
    url = f"{DEST_URL}/api/pam/credential"
    headers = {"Authorization": f"Bearer {token}"}
    log.info("Listando credenciais no vault de destino ...")
    resp = SESSION.get(url, headers=headers, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()
    creds = resp.json().get("credentials", [])
    log.info("%d credencial(is) encontrada(s) no destino.", len(creds))
    return creds


def find_credential(dest_creds, username, hostname, ip):
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
    resp = SESSION.post(url, json=body, headers=headers, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()


def save_report(results, path):
    fieldnames = list(asdict(MigrationResult()).keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    log.info("Relatorio salvo em: %s", path)


def main():
    missing = [name for name, val in [
        ("DEST_URL",    DEST_URL),
        ("DEST_ID",     DEST_ID),
        ("DEST_SECRET", DEST_SECRET),
    ] if not val]

    if missing:
        log.error(
            "Variavel(is) obrigatoria(s) nao definida(s): %s\n"
            "Adicione-as ao .env e tente novamente.",
            ", ".join(missing)
        )
        sys.exit(1)

    token      = get_access_token(DEST_URL, DEST_ID, DEST_SECRET)
    rows       = load_csv(INPUT_CSV)
    dest_creds = list_dest_credentials(token)
    log.info("%d credencial(is) carregada(s) do CSV.", len(rows))

    results = []
    success = skipped = errors = 0

    for idx, row in enumerate(rows, start=1):
        username = row.get("username", "").strip()
        hostname = row.get("hostname", "").strip()
        ip       = row.get("ip",       "").strip()
        password = row.get("password", "").strip()

        log.info("[%d/%d] %s@%s ...", idx, len(rows), username, hostname)
        result = MigrationResult(username=username, hostname=hostname, ip=ip)

        if not password:
            log.warning("  SKIP — password vazia no CSV")
            result.status = "skipped"
            result.detail = "password vazia no CSV"
            skipped += 1
            results.append(result)
            continue

        match = find_credential(dest_creds, username, hostname, ip)
        if not match:
            log.warning("  SKIP — sem correspondencia no destino")
            result.status = "skipped"
            result.detail = "sem correspondencia no destino"
            skipped += 1
            results.append(result)
            continue

        try:
            update_password(token, match, username, hostname, ip, password)
            log.info("  OK — id=%s  identifier=%s", match["id"], match["identifier"])
            result.dest_id    = match["id"]
            result.identifier = match["identifier"]
            result.status     = "success"
            success += 1
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else "?"
            detail = f"HTTP {status_code}: {exc.response.text[:120] if exc.response else ''}"
            log.warning("  Erro: %s", detail)
            result.status = "error"
            result.detail = detail
            errors += 1
        except Exception as exc:
            log.warning("  Erro inesperado: %s", exc)
            result.status = "error"
            result.detail = str(exc)
            errors += 1

        results.append(result)

        if REQUEST_DELAY > 0:
            time.sleep(REQUEST_DELAY)

    save_report(results, REPORT_CSV)
    log.info("Concluido. sucesso=%d  pulados=%d  erros=%d", success, skipped, errors)


if __name__ == "__main__":
    main()