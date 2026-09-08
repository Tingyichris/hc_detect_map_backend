# hcdmap-backend — API + MySQL

Standalone project. REST API + MariaDB/MySQL persistence for the sushi plate tracker. Receives
the fusion server's idempotent result feed, serves the frontend, publishes the map-reload MQTT
signal. Browse the DB at phpMyAdmin (:8080).

```
pip install -e ".[dev]"
docker compose up -d mariadb phpmyadmin
alembic upgrade head
python -m hcdmap_backend        # :8000, Swagger at /docs
pytest
```

See `CLAUDE.md` for layout and rules, `docs/api-contract.md` for the wire contract.
