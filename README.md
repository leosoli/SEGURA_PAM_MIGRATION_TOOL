# SEGURA_PAM_EXPORT_PASSWORDS

Projeto de exportação de senhas armazenadas no módulo PAM Core da solução de Privileged Access Management Segura, com suporte à migração de credenciais entre vaults via API A2A.

## Compatibilidade de versões

| Versão Segura | Endpoint utilizado | Suporte |
|---|---|---|
| 3.33, 4.0, 4.2.x | `/api/*` | ✅ Suportado |
| 3.30, 3.31, 3.32 | `/iso/*` | ✅ Suportado |

> ℹ️ Versões como `4.2.0-6` seguem o padrão `MAJOR.MINOR.PATCH-BUILD` e são tratadas como pertencentes à sua série minor (ex: `4.2`).

## Pré-requisitos

### Vault de origem
- Versão Segura 3.30 ou superior
- Aplicação A2A configurada com permissão de **leitura** em credenciais
- As credenciais a serem exportadas devem estar cadastradas no vault

### Vault de destino
- Versão Segura 3.30 ou superior
- Aplicação A2A configurada com permissão de **leitura e escrita** em credenciais
- As credenciais devem estar **previamente cadastradas** no vault de destino via importação em lote pelo template Excel do Segura (`Batch Import`)
- Os campos `username`, `hostname` e `management ip` devem ser **idênticos** aos do vault de origem — são usados como chave de correspondência durante a migração

> ⚠️ O script **não cria** credenciais no destino. Ele apenas atualiza a senha de credenciais já existentes. Credenciais sem correspondência serão ignoradas e registradas no relatório com status `skipped`.

## Scripts

| Script | Descrição |
|---|---|
| `senhasegura_export.py` | Exporta todas as credenciais e senhas do vault de origem para CSV |
| `senhasegura_migrate.py` | Lê o CSV e atualiza as senhas no vault de destino |
| `api_prefix.py` | Módulo auxiliar — resolve o prefixo do endpoint com base na versão do vault |

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
# atualiza a senha via POST /pam/credential
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
| `SENHASEGURA_VERSION` | export | Sim | — | Versão do vault de origem (ex: `3.31`, `4.2`, `4.2.0-6`) |
| `DEST_URL` | migrate | Sim | — | URL base do vault de destino |
| `DEST_ID` | migrate | Sim | — | Client ID da aplicação A2A de destino |
| `DEST_SECRET` | migrate | Sim | — | Client Secret da aplicação A2A de destino |
| `DEST_VERSION` | migrate | Sim | — | Versão do vault de destino (ex: `3.31`, `4.2`, `4.2.0-6`) |
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