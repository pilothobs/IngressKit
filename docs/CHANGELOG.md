## 2025-08-14

- Add healthcheck endpoints `GET /v1/ping` and `GET /ping` to `server/main.py` returning `{ "message": "pong" }`.
  - Useful for uptime checks and external monitors (e.g., RapidAPI) to verify backend availability.
- Add deployment scripts for systemd/uvicorn:
  - `server/deploy/install_systemd.sh` - initial setup
  - `server/deploy/update.sh` - redeploy code changes  
  - `server/deploy/verify.sh` - test endpoints

