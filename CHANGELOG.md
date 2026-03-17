# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

## [v1.1.0] - 2026-03-17

### Adicionado
- `senhasegura_migrate.py` — migra senhas do CSV de origem para o vault de destino
- Configuração do vault de destino via variáveis `DEST_URL`, `DEST_ID`, `DEST_SECRET`
- Correspondência de credenciais por `username` + `hostname` ou `management_ip`
- Atualização de senha via `POST /api/pam/credential` usando `identifier` como chave de busca e `content` como campo da senha
- Variáveis `INPUT_CSV` e `REPORT_CSV` para configuração dos arquivos de entrada e saída
- Lógica de skip para credenciais com `password` vazia ou sem correspondência no destino
- Relatório de migração salvo em `migration_report.csv` com colunas: `username`, `hostname`, `ip`, `dest_id`, `identifier`, `status`, `detail`
- `migration_report.csv` adicionado ao `.gitignore`
- Supressão de avisos SSL quando `VERIFY_SSL=false`

## [v1.0.0] - 2026-03-17

### Adicionado
- Autenticação OAuth 2.0 via API A2A do senhasegura
- Listagem de todas as credenciais disponíveis via `GET /api/pam/credential`
- Busca do detalhe de cada credencial via `GET /api/pam/credential/{id}`
- Exportação de credenciais e senhas para CSV
- Suporte a `.env` via python-dotenv
- `.env.example` como referência segura de configuração
- Retry HTTP com backoff exponencial (3 tentativas) em erros 429/5xx
- Logging estruturado com timestamp e nível de severidade
- Validação de variáveis de ambiente obrigatórias na inicialização
- Controle de verificação SSL via variável `VERIFY_SSL`
- Delay configurável entre chamadas via variável `REQUEST_DELAY`
- `credentials_export.csv` e todos os CSVs protegidos no `.gitignore`