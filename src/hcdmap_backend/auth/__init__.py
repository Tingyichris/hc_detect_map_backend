"""Auth: users (roles floor|manager), service-token check for ingest, WS token issuance.

STUB. `api/deps.py` currently accepts any non-empty Authorization header as a manager.
Implement:
  - users.py  : user table + password hashing (passlib bcrypt), login endpoint -> JWT
  - tokens.py : JWT encode/decode (pyjwt, settings.jwt_secret), role check dependency,
                short-lived WS token minting for GET /api/ws-token
"""
