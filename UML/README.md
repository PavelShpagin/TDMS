# UML Diagrams for TDMS DBMS

## Project: Table Database Management System
**Variant 58**: date/dateInvl types + Union operation

## Diagram List (10 diagrams total)

### 1. Use Case Diagram (`01_use_case.puml`)
Shows what users can do with the system - create databases, manage tables, save to Google Drive.

### 2. Core Class Diagram (`02_class_core.puml`)
The main classes in the system: Database, Table, Column, Row, TypeValidator, and Operations.

### 3. VOPC Union Diagram (`03_vopc_union.puml`)
View-Object-Persistence-Control for the Union operation (your variant #58 requirement).

### 4. Activity Diagram (`04_activity.puml`)
Step-by-step workflow of creating tables and adding data.

### 5. Sequence: Insert Row (`05_sequence_insert.puml`)
How data gets added to a table with type validation.

### 6. Sequence: Google Drive (`06_sequence_google.puml`)
How saving to and loading from Google Drive works.

### 7. State Diagram (`07_state.puml`)
Different states the system can be in during operation.

### 8. Component Diagram (`08_component.puml`)
Major components and how they connect.

### 9. Deployment Diagram (`09_deployment.puml`)
Where everything runs - local server and Google Cloud.

### 10. Sequence: Union Tables (`10_sequence_union.puml`)
How two tables are combined (variant #58 operation).

## Your Implementation Features

### Supported Data Types
- **Basic**: integer, real, char, string
- **Variant 58**: 
  - `date` - dates in YYYY-MM-DD format
  - `dateInvl` - date intervals with start and end

### Implemented Operations
- Create/switch/delete databases
- Create/drop tables
- Insert rows (with edit_row in core)
- View table data
- **Union tables** (variant 58 special operation)
- Save/load locally
- Save/load to Google Drive

### Google Drive Integration
- Service account authentication
- Upload databases as JSON
- Download and list files
- Configured via environment variables

## Generated Images
All PNG images are in the `images/` folder and ready for viewing.

## How to Regenerate Images
```bash
./generate_simple.sh
```

This uses the PlantUML web service to convert .puml files to PNG images.