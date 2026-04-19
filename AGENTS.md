# Pixel art canvas — agent instructions

## Setup
pip install -r requirements.txt

## Tests
pytest tests/ -v
# Single file: pytest tests/test_routes.py -v

## Project structure
- App entry point: app.py
- Database models: models.py
- Routes: routes/ (one file per feature area)
- Templates: templates/
- Static files: static/
- Tests: tests/

## Do
- Use Flask-SQLAlchemy for all database access
- Use Pillow for PNG export
- Use pytest for all tests
- Keep route handlers thin: business logic belongs in service functions

## Don't
- Do not use print statements for logging
- Do not write raw SQL: use the SQLAlchemy ORM
- Do not add new dependencies without updating requirements.txt

## Safety and permissions
Allowed without asking: read files, run single-file tests, lint
Ask first: deleting files, installing new packages, running the full test suite

## Review guidelines
- Flag any route that modifies data without validating the input
- Flag any database query that could return unbounded results