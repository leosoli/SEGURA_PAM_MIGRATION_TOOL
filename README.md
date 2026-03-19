# SEGURA_PAM_EXPORT_PASSWORDS
Projeto de exportação de senhas armazenadas no módulo PAM Core da solução de Privileged Access Management Segura, com suporte à migração de credenciais entre vaults via API A2A.

## Compatibilidade de versões

| Versão Segura | Endpoint utilizado | Suporte |
|---|---|---|
| 3.33, 4.0, 4.2.x | `/api/*` | ✅ Suportado |
| 3.30, 3.31, 3.32 | `/iso/*` | 🔜 Compatibilidade prevista para versões futuras |

> ℹ️ Versões como `4.2.0-6` seguem o padrão `MAJOR.MINOR.PATCH-BUILD` e são tratadas como pertencentes à sua série minor (ex: `4.2`).

## Scripts

| Script | Descrição |
|---|---|
| `senhasegura_export.py` | Exporta todas as credenciais e senhas do vault de origem para CSV |
| `senhasegura_migrate.py` | Lê o CSV e atualiza as senhas no vault de destino |

## Instalação

```bash
pip install -r requirements.txt
cp .env.example .env
# preencha com as credenciais do seu vault
```

## Exportação

```bash
python senhasegura_export.py
# gera credentials_export.csv
```

## Migração

```bash
python senhasegura_migrate.py
# lê credentials_export.csv
# localiza cada credencial no destino por username + hostname/ip
# atualiza a senha via POST /api/pam/credential
#   - identifier é usado como chave de busca
#   - a senha é enviada no campo content
# gera migration_report.csv
```

## Configuração

| Variável | Usado por | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| `SENHASEGURA_URL` | export | Sim | — | URL base do vault de origem |
| `SENHASEGURA_ID` | export | Sim | — | Client ID da aplicação A2A de origem |
| `SENHASEGURA_SECRET` | export | Sim | — | Client Secret da aplicação A2A de origem |
| `DEST_URL` | migrate | Sim | — | URL base do vault de destino |
| `DEST_ID` | migrate | Sim | — | Client ID da aplicação A2A de destino |
| `DEST_SECRET` | migrate | Sim | — | Client Secret da aplicação A2A de destino |
| `OUTPUT_CSV` | export | Não | `credentials_export.csv` | Arquivo de saída da exportação |
| `INPUT_CSV` | migrate | Não | `credentials_export.csv` | Arquivo de entrada da migração |
| `REPORT_CSV` | migrate | Não | `migration_report.csv` | Arquivo de relatório da migração |
| `REQUEST_DELAY` | ambos | Não | `0.3` | Segundos de espera entre chamadas à API |
| `VERIFY_SSL` | ambos | Não | `true` | Defina `false` para certificados auto-assinados |

## Segurança

> ⚠️ Os CSVs gerados contêm senhas em texto plano.
> Tanto `credentials_export.csv` quanto `migration_report.csv` estão protegidos
> pelo `.gitignore` e jamais devem ser commitados ou compartilhados.

## Changelog

Consulte [CHANGELOG.md](./CHANGELOG.md)