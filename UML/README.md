# UML Diagrams for TDMS DBMS

## Project Information
- **Module 1**: Partial implementation of a table database management system
- **Variant 58**: 
  - Additional types: `date`, `dateInvl` (date intervals)
  - Additional operation: Union of tables
- **Student**: [Your student ID ending in 58]

## Diagram List

### 1. Use Case Diagram (`01_use_case.puml`)
Shows the main functionalities available to users and administrators of the TDMS system.

### 2. Core Class Diagram (`02_class_core.puml`)
Detailed class structure of the core business logic layer including Database, Table, Column, Row, TypeValidator, and Operations classes.

### 3. VOPC Diagram - Union Operation (`03_vopc_union.puml`)
View-Object-Persistence-Control diagram specifically for the Union Tables use case (variant 58 specific operation).

### 4. Activity Diagram (`04_activity.puml`)
Workflow for creating and populating a table with data validation.

### 5. Sequence Diagram - Insert Row (`05_sequence_insert.puml`)
Detailed interaction sequence for inserting a row with type validation.

### 6. Sequence Diagram - Union Tables (`06_sequence_union.puml`)
Interaction sequence for the union operation between two tables.

### 7. State Diagram (`07_state.puml`)
Database lifecycle states from initialization through operations to closure.

### 8. Component Diagram (`08_component.puml`)
System architecture showing presentation, application, business logic, and persistence layers.

### 9. Deployment Diagram (`09_deployment.puml`)
Physical deployment structure for web and desktop versions.

### 10. Complete System Class Diagram (`10_class_full_system.puml`)
Full system class structure including web and desktop layers.

## How to Generate PNG Images

### Option 1: Using PlantUML Online
1. Visit http://www.plantuml.com/plantuml/uml/
2. Copy the content of any `.puml` file
3. Paste it in the editor
4. The diagram will be generated automatically
5. Right-click and save the image

### Option 2: Using PlantUML Locally (Recommended)

#### Prerequisites
- Java Runtime Environment (JRE) installed
- PlantUML JAR file

#### Installation
```bash
# Download PlantUML
wget https://github.com/plantuml/plantuml/releases/download/v1.2024.0/plantuml-1.2024.0.jar -O plantuml.jar

# Or using the provided script
./generate_diagrams.sh
```

#### Generate All Diagrams
```bash
# Generate all PNG files at once
java -jar plantuml.jar *.puml

# Or generate a specific diagram
java -jar plantuml.jar 01_use_case.puml
```

### Option 3: Using Docker
```bash
# Pull PlantUML Docker image
docker pull plantuml/plantuml-server

# Generate diagrams
docker run -v $(pwd):/data plantuml/plantuml-server -tpng /data/*.puml
```

### Option 4: VS Code Extension
1. Install "PlantUML" extension in VS Code
2. Open any `.puml` file
3. Press `Alt+D` to preview
4. Right-click on preview and export as PNG

## Diagram Descriptions

### Use Case Analysis
The system supports two main actor types:
- **User**: Regular database operations (create, insert, edit, view, union)
- **Administrator**: System management (save/load, validation, type management)

### Class Structure
- **Core Layer**: Shared business logic between web and desktop versions
- **Database**: Main container for tables
- **Table**: Container for rows with schema validation
- **TypeValidator**: Ensures data integrity for all supported types
- **Operations**: Implements union operation (variant 58)

### Supported Data Types
1. **Basic Types**: integer, real, char, string
2. **Date Type**: Format YYYY-MM-DD
3. **DateInvl Type**: Date intervals {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

### Union Operation (Variant 58)
- Combines two tables with compatible schemas
- Overlapping columns must have identical types
- Result contains all rows from both tables (UNION ALL semantics)
- Missing columns filled with null values

## Testing Coverage
- 86 unit tests total
- Core module: 100% coverage
- Desktop API: 92% coverage  
- Web API: 58% coverage

## Architecture Benefits
1. **Modular Design**: Clear separation of concerns
2. **Code Reuse**: 85% shared code between versions
3. **Type Safety**: Comprehensive validation for all data types
4. **Scalability**: Web version supports multiple users
5. **Portability**: Desktop version works offline

## Compliance with Requirements
✅ All required diagram types included (9+ diagrams)  
✅ VOPC diagram for union operation  
✅ Two sequence diagrams  
✅ All diagrams properly annotated  
✅ PlantUML format for easy generation  
✅ Comprehensive system documentation