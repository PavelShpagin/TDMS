📄 Project Documentation: Table Database Management System

1. Project Overview

We are developing a partial DBMS (Database Management System) that supports:

multiple tables, unlimited fields and rows;

supported types: integer, real, char, string, and additional variant-specific types;

operations: create/delete database and tables, insert/update rows, validation;

persistence to disk (JSON) and reload;

one individual operation according to the variant (defined by student ID).

Implementation strategy:

Core (Python classes): handles DB logic.

Desktop Client (PyWebview): GUI in a native-like window.

Web Version (FastAPI): REST API + basic HTML templates.

2. Architecture
   2.1 Core Classes

Database: manages multiple tables.

Table: manages schema (columns) and rows.

Column: field definition (name, type).

Row: collection of values.

TypeValidator: validates values for each type.

Operations: module implementing variant-specific operation (sort, union, difference, etc.).

2.2 Technology Stack

Language: Python 3.11+

Desktop GUI: PyWebview

Web: FastAPI + Jinja2 templates

Persistence: JSON (via json module)

Tests: Pytest

3. UML Diagrams to Generate

Use Case Diagram:
Actors: User
Use cases: Create database, Create/Delete table, Insert row, Edit row, View rows, Save/Load database, Variant-specific operation.

Class Diagrams (2+):

Core model: Database, Table, Column, Row.

VOPC diagram for the variant-specific operation.

Activity Diagram (1+):
Example: process of inserting a row (validation → insert → confirm).

Interaction Diagrams (2+):

Sequence diagram: User requests “insert row”.

Sequence diagram: User triggers variant-specific operation.

State Diagram (1+):
Example: Table lifecycle: Created → Modified → Saved → Loaded.

Component Diagram (1+):
Components: GUI, Web API, Core Logic, Persistence.

Deployment Diagram (1+):

Node 1: Desktop client (PyWebview + Core + JSON storage).

Node 2: Web server (FastAPI + Core + JSON storage).

User connects via desktop app or browser.

4. Implementation Roadmap
   Stage 2. Desktop Client (13 pts)

Build the core Python classes (Database, Table, etc.).

Implement PyWebview GUI with menus:

create/delete table, insert/edit rows, run variant operation.

Provide unit tests (3+) with pytest:

Test table creation.

Test row insertion with validation.

Test variant-specific operation (e.g. sorting).

Save/load database from JSON.

Bonus (+5 pts): enable desktop client to talk with the FastAPI server (synchronization).

Stage 3. Web Version (14 pts)

Use FastAPI to expose REST endpoints:

/create_table (POST)

/insert_row (POST)

/view_table (GET)

/operation (POST)

Add HTML templates with Jinja2 for rendering tables.

Use the same core Python library for logic.

Stage 4. Comparative Analysis (1 pt)

Desktop client: fast, works offline, simple GUI.

Web version: accessible anywhere, easier to extend, supports multiple users.

Commonalities: both reuse the same core library and JSON storage.

Differences: deployment, interface, scalability.

Optimal approach: Web version (FastAPI) for scalability, but Desktop version is easier for offline/local usage.

5. Repository Structure (GitHub)
   dbms-project/
   │── src/
   │ ├── core/
   │ │ ├── database.py
   │ │ ├── table.py
   │ │ ├── row.py
   │ │ ├── column.py
   │ │ ├── validator.py
   │ │ └── operations.py
   │ ├── desktop/
   │ │ └── app.py
   │ └── web/
   │ ├── main.py
   │ ├── templates/
   │ │ └── index.html
   │ └── static/
   │── tests/
   │ └── test_core.py
   │── docs/
   │ ├── uml/
   │ └── report.pdf
   │── README.md

6. GitHub README (short draft)

DBMS Project
Partial implementation of a table-based database system.

Core logic in Python.

Desktop GUI: PyWebview.

Web version: FastAPI.

Persistence: JSON.
