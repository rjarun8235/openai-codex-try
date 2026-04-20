---
name: new-route
description: Scaffold a new Flask blueprint route in routes/ with matching service function in services/ and a pytest in tests/. Enforces this repo's thin-handler rule.
---

# Steps
1. Ask the user for the route name (snake_case) and HTTP method.
2. Create `routes/<name>.py` with a blueprint `<name>_bp` registered at `/<name>`.
3. Create `services/<name>_service.py` holding all business logic.
4. The route handler must only: validate input, call the service, return JSON.
5. Register the blueprint in `app.py`.
6. Create `tests/test_<name>.py` with one happy-path test and one invalid-input test using `pytest` + Flask's test client.
7. Run `pytest tests/test_<name>.py -v` and confirm pass.

# Rules
- Use Flask-SQLAlchemy only. No raw SQL.
- No `print`. Use `current_app.logger`.