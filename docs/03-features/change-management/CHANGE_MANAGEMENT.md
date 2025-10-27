Change Management App
=====================

Overview
--------
The `change_management` app provides a simple, central place for stakeholders to file Change Requests, report Incidents, and track Leads. It exposes a small REST API and integrates with Django admin.

Models
------
- `ChangeRequest`: title, description, reporter, assignee, status, priority.
- `Incident`: title, details, reporter, severity, resolved flag.
- `Lead`: basic contact info and owner/notes.

API endpoints
-------------
Under the project root the app mounts the API at `/api/change-management/`:

- `GET /api/change-management/change-requests/` — list change requests
- `POST /api/change-management/change-requests/` — create (authenticated only)
- `GET /api/change-management/incidents/` — list incidents
- `POST /api/change-management/incidents/` — create incident (authenticated only)
- `GET /api/change-management/leads/` — list leads
- `POST /api/change-management/leads/` — create lead (authenticated only)

Permissions
-----------
Read-only access is allowed to anonymous users. Create/update/delete actions require authentication.

Next steps
----------
- Add email/notification hooks for reporters/assignees.
- Add activity logs and comment threads on CRs/incidents.
- Add basic UI templates and integrate into the admin dashboard.
