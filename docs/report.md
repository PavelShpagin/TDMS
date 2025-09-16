TDMS DBMS - Module 1, Variant 58

Architecture Overview

- Core domain implements a minimal table-based DBMS with types: integer, real, char, string, date, dateInvl.
- Persistence uses JSON serialization for Database and Table objects.
- Desktop UI uses PyWebview to render a lightweight HTML interface and expose Python APIs.
- Web UI uses FastAPI with Jinja2 templates; endpoints cover create table, insert row, view, union, save/load.

Design Rationale

- TypeValidator centralizes normalization and validation, returning canonical values (e.g., ISO date strings) for consistent equality semantics.
- Tables keep a schema signature to quickly assert compatibility for operations like union.
- Union uses a deterministic JSON-based key across ordered columns to deduplicate rows reliably, including nested structures like date intervals.

Validation Rules

- integer: int(value), rejects booleans.
- real: float(value), rejects booleans.
- char: one-character string.
- string: any string; bytes decoded as UTF-8.
- date: ISO YYYY-MM-DD using datetime.date.fromisoformat.
- dateInvl: {start,end} pair where start <= end, accepts dict, 2-tuple/list, or "start..end".

Desktop vs Web (Comparative Analysis)
Desktop (PyWebview)

- Advantages: single-file executable potential, OS integration, offline operation, simple deployment for individual users.
- Disadvantages: packaging overhead, UI limited by embedded browser and APIs, distribution/updates per-user.

Web (FastAPI)

- Advantages: centralized deployment, multi-user access, easy scaling, API-first for integrations, browser-based UI.
- Disadvantages: requires server environment, network dependency, additional security and DevOps considerations.

When to choose which

- Desktop for small teams, offline-first tools, and simple distribution.
- Web for multi-user collaboration, centralized data, integrations, and remote access.

Testing Strategy

- Pytest covers: schema creation, row insertion with validation, union operation including deduplication and type handling.

Tools

- Python 3.11+, FastAPI, Jinja2, PyWebview, Pytest.

Future Work

- Additional relational operations (select, project, join).
- Constraints and indexes.
- Authentication and multi-database management.
- Better GUI with schemas/rows forms and validation feedback.
