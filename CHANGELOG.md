# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

## [v1.2.0] - 2026-03-18

### Adicionado
- Suporte a vaults Segura versões 3.30, 3.31 e 3.32 via endpoint `/iso/`
- `api_prefix.py` — módulo auxiliar que resolve automaticamente o prefixo correto (`/api` ou `/iso`) com base na versão configurada
- Variável `SENHASEGURA_VERSION` no `.env` para definir a versão do vault de origem
- Variável `DEST_VERSION` no `.env` para definir a versão do vault de destino
- Suporte a strings de versão no formato `MAJOR.MINOR.PATCH-BUILD` (ex: `4.2.0-6`)

### Documentação
- Tabela de compatibilidade atualizada — ambos os endpoints `/api/*` e `/iso/*` agora marcados como suportados
- Pré-requisitos atualizados — versão mínima alterada de 3.33 para 3.30
- `api_prefix.py` adicionado à tabela de scripts

## [v1.1.2] - 2026-03-18

### Documentação
- Adicionada tabela de compatibilidade de versões do Segura com os endpoints `/api/*` e `/iso/*`
- Nota sobre o padrão de versionamento `MAJOR.MINOR.PATCH-BUILD` (ex: `4.2.0-6`)
- Adicionada seção de pré-requisitos separando vault de origem e destino
- Documentado que as credenciais do destino devem ser previamente cadastradas via Batch Import do Segura
- Documentado que `username`, `hostname` e `management ip` devem ser idênticos entre os dois vaults
- Documentado que o script não cria credenciais — apenas atualiza senhas de credenciais existentes

## [v1.1.1] - 2026-03-17

### Corrigido
- Supressão de avisos SSL em `senhasegura_export.py` quando `VERIFY_SSL=false`, alinhando o comportamento com `senhasegura_migrate.py`

## [v1.1.0] - 2026-03-17

### Adicionado
- `senhasegura_migrate.py` — migra senhas do CSV de origem para o vault de destino
- Configuração do vault de destino via variáveis `DEST_URL`, `DEST_ID`, `DEST_SECRET`
- Correspondência de credenciais por `username` + `hostname` ou `management_ip`
- Atualização de senha via `POST /pam/credential` usando `identifier` como chave de busca e `content` como campo da senha
- Variáveis `INPUT_CSV` e `REPORT_CSV` para configuração dos arquivos de entrada e saída
- Lógica de skip para credenciais com `password` vazia ou sem correspondência no destino
- Relatório de migração salvo em `migration_report.csv`
- `migration_report.csv` adicionado ao `.gitignore`
- Supressão de avisos SSL quando `VERIFY_SSL=false`

## [v1.0.0] - 2026-03-17

### Adicionado
- Autenticação OAuth 2.0 via API A2A do senhasegura
- Listagem de todas as credenciais disponíveis
- Busca do detalhe de cada credencial incluindo senha
- Exportação de credenciais e senhas para CSV
- Suporte a `.env` via python-dotenv
- `.env.example` como referência segura de configuração
- Retry HTTP com backoff exponencial (3 tentativas) em erros 429/5xx
- Logging estruturado com timestamp e nível de severidade
- Validação de variáveis de ambiente obrigatórias na inicialização
- Controle de verificação SSL via variável `VERIFY_SSL`
- Delay configurável entre chamadas via variável `REQUEST_DELAY`
- `credentials_export.csv` e todos os CSVs protegidos no `.gitignore`