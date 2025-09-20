# Hawwa Wellness

Hawwa Wellness (formerly Hawwa Postpartum Care) — a platform for postpartum care coordination, provider marketplace, and wellness services.

Quickstart (demo)

1. Copy demo environment:

```bash
cp .env.demo.example .env
```

2. Start demo stack with Docker Compose:

```bash
docker compose -f docker-compose.demo.yml up --build
```

3. Visit http://localhost:8000

Repository contents
- `change_management/` — Change Requests, Incidents, Leads, comments, activity
- `bookings/`, `vendors/`, `payments/`, `accounts/` — core apps
- `docs/` — documentation and startup application materials

Contributing
See `CONTRIBUTING.md` for guidelines.

License
This project is available under the MIT License (see `LICENSE`).
