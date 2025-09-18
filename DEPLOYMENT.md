# TDMS Deployment Guide

## Production Deployment

### Web Version

#### Requirements

- Python 3.8+
- FastAPI dependencies: `pip install fastapi[all] python-dotenv`

#### Setup

1. **Environment Variables**: Create `.env` file with:

   ```
   GOOGLE_OAUTH_CLIENT_ID=your_web_client_id
   GOOGLE_OAUTH_CLIENT_SECRET=your_web_client_secret
   GOOGLE_API_KEY=your_api_key (optional)
   GOOGLE_PICKER_APP_ID=your_picker_app_id (optional)
   ```

2. **Google Cloud Console**:

   - Create Web Application OAuth 2.0 client
   - Add authorized redirect URIs: `http://your-domain.com/oauth/callback`
   - Enable Google Drive API

3. **Deploy**:
   ```bash
   uvicorn src.web.main:app --host 0.0.0.0 --port 8000
   ```

### Desktop Version

#### Requirements

- Python 3.8+
- Dependencies: `pip install fastapi[all] pywebview python-dotenv`

#### Setup

1. **Environment Variables**: Create `.env` file with:

   ```
   DESKTOP_GOOGLE_OAUTH_CLIENT_ID=your_desktop_client_id
   DESKTOP_GOOGLE_OAUTH_CLIENT_SECRET=your_desktop_client_secret
   ```

2. **Google Cloud Console**:

   - Create Desktop Application OAuth 2.0 client
   - No redirect URIs needed (uses OOB flow)

3. **Run**:
   ```bash
   python -m src.desktop.simple_app
   ```

#### Build Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name TDMS src/desktop/simple_app.py
```

## Features

### Core Functionality

- ✅ Database creation and management
- ✅ Table operations (create, edit, delete)
- ✅ Data import/export
- ✅ Google Drive integration
- ✅ Professional UI without emojis

### Google Drive Integration

- ✅ OAuth 2.0 authentication
- ✅ File upload to Google Drive
- ✅ File download from Google Drive
- ✅ Duplicate name handling (auto-suffix)
- ✅ Standard Google Drive picker

### Database Management

- ✅ Sorted by modification time (newest first)
- ✅ Persistent file storage
- ✅ Automatic save on changes
- ✅ Clean deletion (removes files)

## Architecture

### Code Sharing (95%+)

- **Backend**: Single FastAPI application
- **Frontend**: Unified HTML template
- **Core Logic**: Shared database operations
- **APIs**: Common REST endpoints

### Platform-Specific (5%)

- **Desktop**: PyWebView wrapper + system browser integration
- **Web**: Standard web deployment

## Security

### OAuth Configuration

- Separate client IDs for web and desktop
- Secure credential storage in `.env`
- Minimal required scopes (`drive.file`)

### Data Storage

- Local JSON file storage
- Automatic backup on Google Drive
- No sensitive data in source code

## Maintenance

### Updates

- Single codebase for both platforms
- Shared bug fixes and features
- Consistent user experience

### Monitoring

- Clean console output (no debug messages)
- Professional error messages
- Simplified user instructions
