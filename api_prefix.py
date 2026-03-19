"""
api_prefix.py
=============
Resolve o prefixo correto do endpoint da API Segura
com base na versao do vault configurada.

Versoes suportadas:
  3.33, 4.0, 4.2.x e superiores → /api
  3.30, 3.31, 3.32               → /iso

Uso:
  from api_prefix import api_prefix
  prefix = api_prefix("4.2.0-6")  # returns "/api"
  prefix = api_prefix("3.31")     # returns "/iso"
"""

import logging

log = logging.getLogger(__name__)


def api_prefix(version: str) -> str:
    """
    Returns the correct API path prefix based on vault version.
      3.33, 4.0, 4.2.x and above → /api
      3.30, 3.31, 3.32            → /iso
    Version strings like '4.2.0-6' are parsed by major.minor only.
    """
    try:
        parts = version.split("-")[0].split(".")
        major, minor = int(parts[0]), int(parts[1])
    except (IndexError, ValueError):
        log.warning("Versao invalida '%s', usando prefixo /api por padrao.", version)
        return "/api"

    if (major == 3 and minor >= 33) or major >= 4:
        return "/api"
    return "/iso"