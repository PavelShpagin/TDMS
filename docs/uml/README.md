# TDMS UML Diagrams

## Overview

This directory contains comprehensive UML diagrams for the TDMS (Table Database Management System) project, created using Mermaid syntax for maintainability and version control.

## Diagram Files

### Core UML Diagrams (Required)

1. **use_case.mmd** - Use Case Diagram showing user interactions with both web and desktop versions
2. **class.mmd** - Class Diagram depicting the complete system architecture with all classes and relationships
3. **activity.mmd** - Activity Diagram showing the complete application workflow from startup to shutdown
4. **sequence_insert.mmd** - Sequence Diagram for row insertion with validation and auto-save
5. **sequence_union.mmd** - Sequence Diagram for table union operations with schema validation
6. **sequence_google_drive.mmd** - Sequence Diagram for Google Drive integration (OAuth + file operations)
7. **sequence_row_edit.mmd** - Sequence Diagram for row editing with date/dateInvl support
8. **state.mmd** - State Diagram showing application states and transitions
9. **component.mmd** - Component Diagram showing system architecture and dependencies
10. **deployment.mmd** - Deployment Diagram showing both desktop and web deployment scenarios

## Current System Features Covered

### Functional Features

- ✅ Database management (create, delete, rename, switch)
- ✅ Table operations (create, delete, view, list)
- ✅ Row operations (insert, edit, update, delete)
- ✅ Union operations with schema validation
- ✅ Data type validation (integer, real, char, string, date, dateInvl)
- ✅ Google Drive integration (OAuth, upload, download)
- ✅ JSON persistence with auto-save
- ✅ Duplicate name handling with suffixes

### Technical Features

- ✅ Desktop application (PyWebView + embedded FastAPI)
- ✅ Web application (standalone FastAPI server)
- ✅ Shared core business logic (85% code reuse)
- ✅ Comprehensive error handling
- ✅ Authentication and authorization
- ✅ Cross-platform compatibility

## Generation Instructions

### Automatic Generation (Recommended)

#### Windows:

```batch
export_uml.bat
```

#### Linux/macOS:

```bash
python3 generate_diagrams.py
```

### Manual Generation

1. **Install Mermaid CLI:**

   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. **Generate individual diagrams:**

   ```bash
   mmdc -i use_case.mmd -o images/use_case.png -t neutral -b white --width 1200 --height 800
   ```

3. **Generate all diagrams:**
   ```bash
   for file in *.mmd; do
     mmdc -i "$file" -o "images/${file%.mmd}.png" -t neutral -b white --width 1200 --height 800
   done
   ```

## Output

Generated PNG files are saved in the `images/` subdirectory:

- `images/use_case.png`
- `images/class.png`
- `images/activity.png`
- `images/sequence_insert.png`
- `images/sequence_union.png`
- `images/sequence_google_drive.png`
- `images/sequence_row_edit.png`
- `images/state.png`
- `images/component.png`
- `images/deployment.png`

## Diagram Quality

All diagrams are generated with:

- **Theme:** Neutral (clean, professional appearance)
- **Background:** White
- **Resolution:** 1200x800 pixels
- **Format:** PNG with transparency support

## Maintenance

The Mermaid source files (.mmd) are the authoritative source. When updating diagrams:

1. Edit the .mmd file
2. Regenerate the PNG using the scripts
3. Commit both the .mmd source and generated .png files

## Integration with Documentation

These diagrams support the academic analysis in the main README.md, providing visual documentation for:

- System architecture decisions
- Component interactions
- User workflow patterns
- Deployment strategies
- State management approach

The diagrams reflect the current implementation as of the latest commit and include all major features including Google Drive integration, row editing capabilities, and the hybrid desktop/web architecture.
