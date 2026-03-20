"""
compare_credentials.py
======================
Compares credentials_export.csv against the scope xlsx spreadsheet
to validate that the export captured the correct credentials.

Expected xlsx columns (exported from senhasegura UI):
  IP, ID, Device, Name, Planilha import, Nome Igual, Importar,
  Username, Type, Just in time, Additional, Domain, Cred Tags,
  Dev Tags, Managed?, Template, Status, Execution date, Last attempt

Column mapping:
  IP       → management_ip of the credential
  ID       → credential ID in the vault
  Name     → device name the credential belongs to
  Username → credential username

Match key: ID + Username + IP (all three must match)

Output:
  - Terminal summary
  - comparison_report.csv with status per credential

Status values:
  matched      — found in both files with correct ID + username + ip
  missing      — in xlsx scope but NOT in export CSV
  ghost        — in export CSV, same username+ip exists in xlsx
                 but with a different ID — confirmed orphaned database
                 entry authorized in A2A instead of the real credential
                 action: remove from A2A and re-authorize with correct ID
  out_of_scope — in export CSV but no match at all in xlsx
                 (not even username+ip) — was authorized in A2A
                 but is outside the defined migration scope

Usage:
  python compare_credentials.py
"""

import csv
import os
import sys
import logging
from dataclasses import dataclass, asdict

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_path(filename: str) -> str:
    if os.path.isabs(filename):
        return filename
    return os.path.join(BASE_DIR, filename)


SCOPE_XLSX        = resolve_path(os.getenv("SCOPE_XLSX",        "scope.xlsx"))
SCOPE_SHEET       = os.getenv("SCOPE_SHEET",       "Sheet1")
OUTPUT_CSV        = resolve_path(os.getenv("OUTPUT_CSV",        "credentials_export.csv"))
COMPARISON_REPORT = resolve_path(os.getenv("COMPARISON_REPORT", "comparison_report.csv"))

# ── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Result model ──────────────────────────────────────────────────────
@dataclass
class ComparisonResult:
    id:       str = ""
    username: str = ""
    ip:       str = ""
    hostname: str = ""
    status:   str = ""   # matched | missing | ghost | out_of_scope
    detail:   str = ""


# ── Load xlsx scope ───────────────────────────────────────────────────
def load_xlsx_scope(path: str, sheet_name: str) -> list:
    """
    Reads the xlsx exported from senhasegura UI.
    Uses columns: IP, ID, Name, Username.
    All other columns are ignored.
    """
    if not os.path.exists(path):
        log.error("Arquivo xlsx nao encontrado: %s", path)
        sys.exit(1)

    log.info("Lendo planilha: %s  aba: %s", path, sheet_name)
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)
    except Exception as exc:
        log.error("Erro ao ler planilha: %s", exc)
        sys.exit(1)

    df.columns = [c.strip() for c in df.columns]

    log.info("Colunas encontradas: %s", list(df.columns))

    required_cols = {"IP", "ID", "Name", "Username"}
    missing_cols  = required_cols - set(df.columns)
    if missing_cols:
        log.error(
            "Colunas obrigatorias ausentes na planilha: %s",
            ", ".join(missing_cols),
        )
        sys.exit(1)

    records = []
    for _, row in df.iterrows():
        cred_id  = str(row.get("ID",       "")).strip()
        username = str(row.get("Username", "")).strip()
        ip       = str(row.get("IP",       "")).strip()
        hostname = str(row.get("Name",     "")).strip()

        if not cred_id or not username or not ip:
            continue

        records.append({
            "id":       cred_id,
            "username": username.lower(),
            "ip":       ip,
            "hostname": hostname,
        })

    log.info("%d credencial(is) carregada(s) da planilha.", len(records))
    return records


# ── Load export CSV ───────────────────────────────────────────────────
def load_export_csv(path: str) -> list:
    if not os.path.exists(path):
        log.error("Arquivo CSV nao encontrado: %s", path)
        sys.exit(1)

    records = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            cred_id  = str(row.get("id",      "")).strip()
            username = str(row.get("username", "")).strip()
            ip       = str(row.get("ip",       "")).strip()
            hostname = str(row.get("hostname", "")).strip()

            if not cred_id or not username or not ip:
                continue

            records.append({
                "id":       cred_id,
                "username": username.lower(),
                "ip":       ip,
                "hostname": hostname,
            })

    log.info("%d credencial(is) carregada(s) do CSV.", len(records))
    return records


# ── Match key ─────────────────────────────────────────────────────────
def match_key(record: dict) -> str:
    """
    Composite key: id|username|ip
    All three must match for a credential to be considered correct.
    Distinguishes real credentials from ghosts that share
    the same username/ip but have a different (lower) ID.
    """
    return f"{record['id']}|{record['username']}|{record['ip']}"


# ── Compare ───────────────────────────────────────────────────────────
def compare(scope: list, exported: list) -> list:
    scope_keys    = {match_key(r): r for r in scope}
    exported_keys = {match_key(r): r for r in exported}
    results       = []

    # Credentials in scope
    for key, rec in scope_keys.items():
        if key in exported_keys:
            results.append(ComparisonResult(
                id=rec["id"], username=rec["username"],
                ip=rec["ip"], hostname=rec["hostname"],
                status="matched", detail="",
            ))
        else:
            partial = f"{rec['username']}|{rec['ip']}"
            ghost   = next(
                (e for e in exported
                 if f"{e['username']}|{e['ip']}" == partial),
                None
            )
            detail = (
                f"Exportado com ID errado: {ghost['id']} "
                f"(esperado: {rec['id']}) — possivel credencial fantasma"
                if ghost else
                "Nao exportado — credencial ausente no CSV"
            )
            results.append(ComparisonResult(
                id=rec["id"], username=rec["username"],
                ip=rec["ip"], hostname=rec["hostname"],
                status="missing", detail=detail,
            ))

    # Credentials exported but not in scope
    for key, rec in exported_keys.items():
        if key not in scope_keys:
            partial     = f"{rec['username']}|{rec['ip']}"
            scope_match = next(
                (s for s in scope
                 if f"{s['username']}|{s['ip']}" == partial),
                None
            )
            if scope_match:
                # Same username+ip exists in scope but different ID
                # → confirmed orphaned database entry (ghost)
                results.append(ComparisonResult(
                    id=rec["id"], username=rec["username"],
                    ip=rec["ip"], hostname=rec["hostname"],
                    status="ghost",
                    detail=(
                        f"ID fantasma: {rec['id']} "
                        f"(ID correto na planilha: {scope_match['id']}) — "
                        f"remover do A2A e reautorizar com ID correto"
                    ),
                ))
            else:
                # No match at all in xlsx — authorized but outside scope
                results.append(ComparisonResult(
                    id=rec["id"], username=rec["username"],
                    ip=rec["ip"], hostname=rec["hostname"],
                    status="out_of_scope",
                    detail="Credencial autorizada no A2A fora do escopo de migracao",
                ))

    return results


# ── Save report ───────────────────────────────────────────────────────
def save_report(results: list, path: str) -> None:
    fieldnames = list(asdict(ComparisonResult()).keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    log.info("Relatorio salvo em: %s", path)


# ── Terminal summary ──────────────────────────────────────────────────
def print_summary(results: list) -> None:
    matched      = [r for r in results if r.status == "matched"]
    missing      = [r for r in results if r.status == "missing"]
    ghosts       = [r for r in results if r.status == "ghost"]
    out_of_scope = [r for r in results if r.status == "out_of_scope"]

    log.info("─" * 60)
    log.info("RESUMO DA COMPARACAO")
    log.info("─" * 60)
    log.info("  Corretos      (matched)      : %d", len(matched))
    log.info("  Ausentes      (missing)      : %d", len(missing))
    log.info("  Fantasmas     (ghost)        : %d", len(ghosts))
    log.info("  Fora do escopo (out_of_scope): %d", len(out_of_scope))
    log.info("─" * 60)

    if missing:
        log.warning("Credenciais ausentes no CSV:")
        for r in missing:
            log.warning("  id=%-6s  %-30s  ip=%s  %s",
                        r.id, r.username, r.ip, r.detail)

    if ghosts:
        log.warning("Credenciais fantasmas (ID errado no A2A):")
        for r in ghosts:
            log.warning("  id=%-6s  %-30s  ip=%s  %s",
                        r.id, r.username, r.ip, r.detail)

    if out_of_scope:
        log.warning("Credenciais fora do escopo de migracao:")
        for r in out_of_scope:
            log.warning("  id=%-6s  %-30s  ip=%s  %s",
                        r.id, r.username, r.ip, r.detail)


# ── Main ──────────────────────────────────────────────────────────────
def main() -> None:
    log.info("Arquivo de escopo : %s  [aba: %s]", SCOPE_XLSX, SCOPE_SHEET)
    log.info("CSV de exportacao : %s", OUTPUT_CSV)

    scope    = load_xlsx_scope(SCOPE_XLSX, SCOPE_SHEET)
    exported = load_export_csv(OUTPUT_CSV)
    results  = compare(scope, exported)

    save_report(results, COMPARISON_REPORT)
    print_summary(results)

    if any(r.status != "matched" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()