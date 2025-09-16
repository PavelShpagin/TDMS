TDMS DBMS – Module 1, Variant 58

# Original Assignment (excerpt)

System Type 1: Partial implementation of a table-based DBMS.

- Unlimited number of tables, columns, rows.
- Required base types: integer, real, char, string.
- Additional types (Variant 58): date, dateInvl.
- Required operation (Variant 58): union of tables.
- Must support: create/delete database, create/delete tables, insert/edit rows with validation, save/load database from disk (JSON).
- Stage 1: UML diagrams (use case, class, activity, 2 sequence, state, component, deployment).
- Stage 2: Desktop version with GUI, 3+ unit tests (one must test the union operation), illustrated report.
- Stage 3: Web version (REST or GraphQL or gRPC, choose REST/FASTAPI).
- Stage 4: Comparative analysis of desktop vs web.
- # Deadline: 08.10.2025

Project Description
This project implements a minimal table-based DBMS core with schema validation, JSON persistence, a PyWebview desktop client, and a FastAPI web app. Variant 58 adds data types `date` and `dateInvl` and requires the `union` operation between tables with identical schemas.

Project Structure

```
dbms-project/
│── src/
│   ├── core/
│   │   ├── database.py
│   │   ├── table.py
│   │   ├── row.py
│   │   ├── column.py
│   │   ├── validator.py
│   │   └── operations.py
│   ├── desktop/
│   │   └── app.py
│   └── web/
│       ├── main.py
│       ├── templates/
│       │   └── index.html
│       └── static/
│── tests/
│   └── test_core.py
│── docs/
│   ├── uml/
│   │   ├── *.mmd (Mermaid sources)
│   │   └── *.png (export locally)
│   └── report.md
│── README.md
│── requirements.txt
```

Run Desktop Version

```bash
pip install -r requirements.txt
python src/desktop/app.py
```

Run Web Version

```bash
uvicorn src.web.main:app --reload
```

Run Tests

```bash
pytest tests/
```

UML Diagrams

- Mermaid `.mmd` sources are in `docs/uml/`. Export PNGs using mermaid-cli and place them in the same folder as required.

Report

- See `docs/report.md` for architecture, design, and desktop vs web analysis.

GitHub Repository

- Placeholder: https://github.com/your-org/dbms-project
