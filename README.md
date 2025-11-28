# Library API (Flask + JWT + Celery + Docker)

## Quick start
```bash
docker compose up -d --build
# seed sample data
docker compose exec api python seed.py
# test login
http POST :8080/auth/login email=test@example.com password=secret
```
Use the access token to call protected endpoints.

## Endpoints
- POST `/auth/login` → returns access_token, refresh_token
- GET `/auth/me` (Bearer)
- GET `/catalog/books?q=search`
- POST `/waitlist` (Bearer) `{ "book_id": 1 }` → 202 Accepted (async hold)
- POST `/waitlist/{id}/confirm` (Bearer)
- POST `/waitlist/{id}/cancel` (Bearer)

## Environment
See `.env.example`. Copy to `.env` and adjust secrets in production.

## Notes
- Tables are auto-created on first run.
- Celery orchestrates waitlist hold/confirm/cancel.
