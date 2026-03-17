# Changelog

All notable changes to this project will be documented in this file.

## [v1.0.0] - 2026-03-17

### Added
- OAuth 2.0 authentication against senhasegura A2A API
- List all available credentials via `GET /api/pam/credential`
- Fetch password detail per credential via `GET /api/pam/credential/{id}`
- Export credentials and passwords to CSV
- dotenv support via `.env` file
- `.env.example` as safe configuration reference
- HTTP retry logic with exponential backoff (3 attempts)
- Structured logging with timestamps and severity levels
- Validation of required environment variables on startup
- SSL verification toggle via `VERIFY_SSL` env var
- Configurable request delay via `REQUEST_DELAY` env var
- `credentials_export.csv` and all CSVs protected in `.gitignore`
