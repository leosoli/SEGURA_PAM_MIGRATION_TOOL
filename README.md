# SEGURA_PAM_EXPORT_PASSWORDS
Projeto de Exportação de senhas armazenadas no módulo PAM Core da solução de Privilege Access Management Segura

Exporta todas as credenciais disponíveis do senhasegura PAM para um arquivo CSV,
utilizando a API A2A (OAuth 2.0 + PAM Core).

## Pré-requisitos

- Python 3.10+
- Acesso à API A2A do senhasegura com permissão de leitura em credenciais

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

```bash
cp .env.example .env
# edite o .env com os valores reais
```

| Variável             | Obrigatória | Descrição                              |
|----------------------|-------------|----------------------------------------|
| SENHASEGURA_URL      | Sim         | URL base do vault (sem barra final)    |
| SENHASEGURA_ID       | Sim         | Client ID da aplicação A2A             |
| SENHASEGURA_SECRET   | Sim         | Client Secret da aplicação A2A         |
| OUTPUT_CSV           | Não         | Nome do arquivo de saída (padrão: credentials_export.csv) |
| REQUEST_DELAY        | Não         | Delay entre chamadas em segundos (padrão: 0.3) |
| VERIFY_SSL           | Não         | Verificar certificado SSL (padrão: true) |

## Uso

```bash
python senhasegura_export.py
```

O arquivo `credentials_export.csv` será gerado na pasta atual.

> ⚠️ O CSV contém senhas em texto plano. O arquivo está no `.gitignore`
> e nunca deve ser versionado ou compartilhado.

## Colunas do CSV

`id`, `identifier`, `username`, `hostname`, `ip`, `port`, `domain`,
`model`, `password`, `expiration_time`, `additional`, `error`
