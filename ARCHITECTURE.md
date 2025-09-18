# TDMS Architecture - Clean Code Sharing

## Overview

TDMS uses a unified architecture where web and desktop versions share 95%+ of the codebase, ensuring consistency and maintainability.

## Code Sharing Structure

### Shared Components (95% of codebase)

- **Backend Logic**: `src/web/main.py` - FastAPI server used by both versions
- **Core Database**: `src/core/` - All database operations and logic
- **Frontend Interface**: `src/web/templates/index.html` - Single UI for both versions
- **API Endpoints**: All REST endpoints shared between web and desktop
- **Google Drive Integration**: Unified OAuth and Drive API handling

### Platform-Specific Modules (5% of codebase)

#### Web Version (`src/web/`)

- **Deployment**: Standard FastAPI web server
- **Access**: Direct browser access via HTTP
- **OAuth**: Browser-based Google OAuth flow

#### Desktop Version (`src/desktop/`)

- **Wrapper**: `simple_app.py` - PyWebView wrapper around web interface
- **Server**: Embedded FastAPI server on local port
- **OAuth**: System browser integration for Google OAuth
- **Distribution**: Standalone executable

## Key Benefits

### 1. Code Consistency

- Same UI/UX across platforms
- Identical feature set
- Single codebase to maintain

### 2. Development Efficiency

- Fix bugs once, applies to both versions
- Add features once, available everywhere
- Single test suite covers both platforms

### 3. Clean Separation

- **Desktop-specific**: Only PyWebView integration and system browser bridge
- **Web-specific**: Only deployment configuration
- **Shared**: Everything else (95%+ of functionality)

## Architecture Decisions

### Database Sorting

- Databases sorted by modification time (newest first)
- Consistent ordering across web and desktop
- No shuffling on refresh

### Professional Appearance

- All emojis removed from codebase
- Clean, professional interface
- Consistent styling and messaging

### OAuth Integration

- Desktop: System browser + manual code entry
- Web: Browser-based OAuth flow
- Both use same Google Drive API integration

## File Structure

```
src/
├── core/           # Shared database logic
├── web/
│   ├── main.py     # Shared FastAPI backend
│   └── templates/
│       └── index.html  # Shared frontend
└── desktop/
    └── simple_app.py   # Desktop-specific wrapper (minimal)
```

This architecture ensures maximum code reuse while maintaining clean separation of platform-specific concerns.
