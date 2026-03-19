"""
senhasegura API - Exportador de Credenciais para CSV
=====================================================
Conecta à API PAM Core (A2A) do senhasegura usando OAuth 2.0,
lista todas as credenciais disponíveis, busca a senha de cada uma
e salva o resultado em credentials_export.csv.

Versoes suportadas:
  - 3.33, 4.0, 4.2.x → endpoint /api/
  - 3.30, 3.31, 3.32  → endpoint /iso/

Pre-requisitos:
  pip install -r requirements.txt

Configuracao:
  Copie .env.example para .env e preencha com os valores reais.
"""


import os
import sys
import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util.retry import Retry
import time
import logging
from dataclasses import dataclass, asdict
import csv
from api_prefix import api_prefix
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# CONFIG — lido do arquivo .env
# ──────────────────────────────────────────────
BASE_URL      = os.getenv("SENHASEGURA_URL")
CLIENT_ID     = os.getenv("SENHASEGURA_ID")
CLIENT_SECRET = os.getenv("SENHASEGURA_SECRET")
VERSION       = os.getenv("SENHASEGURA_VERSION", "4.2")

OUTPUT_CSV    = os.getenv("OUTPUT_CSV", "credentials_export.csv")
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.3"))
VERIFY_SSL    = os.getenv("VERIFY_SSL", "true").lower() != "false"
# ──────────────────────────────────────────────

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


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



def build_session() -> requests.Session:
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



def get_access_token(prefix: str) -> str:
    url = f"{BASE_URL}{prefix}/oauth2/token"
    payload = {
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    log.info("Autenticando via OAuth 2.0 em %s ...", url)
    try:
        resp = SESSION.post(url, data=payload, verify=VERIFY_SSL, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.SSLError:
        log.error("Erro SSL. Defina VERIFY_SSL=false para certificados auto-assinados.")
        sys.exit(1)
    except requests.exceptions.ConnectionError as exc:
        log.error("Nao foi possivel conectar em %s: %s", BASE_URL, exc)
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





def list_credentials(token: str, prefix: str) -> list:
    url = f"{BASE_URL}{prefix}/pam/credential"
    headers = {"Authorization": f"Bearer {token}"}
    log.info("Buscando lista de credenciais ...")
    resp = SESSION.get(url, headers=headers, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()
    credentials = resp.json().get("credentials", [])
    log.info("%d credencial(is) encontrada(s).", len(credentials))
    return credentials




def get_credential_detail(token: str, cred_id: str, prefix: str) -> dict:
    url = f"{BASE_URL}{prefix}/pam/credential/{cred_id}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = SESSION.get(url, headers=headers, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()
    return resp.json().get("credential", {})



def export_to_csv(credentials: list, path: str) -> None:
    fieldnames = list(asdict(Credential()).keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for cred in credentials:
            writer.writerow(asdict(cred))
    log.info("CSV salvo em: %s  (%d linha(s))", path, len(credentials))




def main() -> None:
    missing = [name for name, val in [
        ("SENHASEGURA_URL",     BASE_URL),
        ("SENHASEGURA_ID",      CLIENT_ID),
        ("SENHASEGURA_SECRET",  CLIENT_SECRET),
        ("SENHASEGURA_VERSION", VERSION),
    ] if not val]

    if missing:
        log.error(
            "Variavel(is) obrigatoria(s) nao definida(s): %s\n"
            "Adicione-as ao .env e tente novamente.",
            ", ".join(missing)
        )
        sys.exit(1)

    prefix = api_prefix(VERSION)
    log.info("Vault de origem: versao=%s  prefixo=%s", VERSION, prefix)

    token    = get_access_token(prefix)
    raw_list = list_credentials(token, prefix)
    results  = []

    for idx, item in enumerate(raw_list, start=1):
        cred_id = str(item.get("id", ""))
        log.info("[%d/%d] Detalhando credencial id=%s ...", idx, len(raw_list), cred_id)

        cred = Credential(
            id=cred_id,
            identifier=item.get("identifier", ""),
            username=item.get("username", ""),
            hostname=item.get("hostname", ""),
            ip=item.get("management_ip", ""),
        )

        try:
            detail = get_credential_detail(token, cred_id, prefix)
            cred.password        = detail.get("password", "")
            cred.port            = detail.get("port", "")
            cred.domain          = detail.get("domain", "")
            cred.model           = detail.get("model", "")
            cred.expiration_time = detail.get("expiration_time", "")
            cred.additional      = detail.get("additional", "")
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response else "?"
            msg = f"HTTP {status}"
            log.warning("  Nao foi possivel obter detalhes: %s", msg)
            cred.error = msg
        except Exception as exc:
            log.warning("  Erro inesperado: %s", exc)
            cred.error = str(exc)

        results.append(cred)

        if REQUEST_DELAY > 0:
            time.sleep(REQUEST_DELAY)

    export_to_csv(results, OUTPUT_CSV)
    log.info("Concluido. %d credencial(is) exportada(s).", len(results))


if __name__ == "__main__":
    main()