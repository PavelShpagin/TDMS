# TDMS Setup Guide

## Google Cloud Console Setup

### 1. Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**

### 2. Create Two OAuth Clients

#### Desktop Application Client
- **Application type**: Desktop application
- **Name**: TDMS Desktop
- **Download** the JSON file and save it in the `secrets/` folder

#### Web Application Client  
- **Application type**: Web application
- **Name**: TDMS Web
- **Authorized redirect URIs**: `http://localhost:8000/oauth/callback`
- **Download** the JSON file and save it in the `secrets/` folder

### 3. Enable APIs
- Enable **Google Drive API** for your project

## Environment Configuration

Create a `.env` file in the project root with your credentials:

```env
# Desktop OAuth credentials (from desktop client JSON)
DESKTOP_GOOGLE_OAUTH_CLIENT_ID=your_desktop_client_id.apps.googleusercontent.com
DESKTOP_GOOGLE_OAUTH_CLIENT_SECRET=your_desktop_client_secret

# Web OAuth credentials (from web client JSON)
GOOGLE_OAUTH_CLIENT_ID=your_web_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_web_client_secret

# Google Picker App ID (project number from client ID)
GOOGLE_PICKER_APP_ID=your_project_number

# Optional: Google API Key
GOOGLE_API_KEY=your_api_key_if_you_have_one
```

## Finding Your Values

### Client ID and Secret
- Found in the downloaded JSON files from Google Cloud Console
- Desktop client: `"client_id"` and `"client_secret"` fields
- Web client: `"client_id"` and `"client_secret"` fields

### Picker App ID
- Extract the project number from your client ID
- Example: If client ID is `123456789-abc123.apps.googleusercontent.com`
- Then Picker App ID is `123456789`

## Security Notes

- Never commit the `.env` file to Git
- Keep your JSON credential files in the `secrets/` folder (also not committed)
- The `.gitignore` file already excludes these sensitive files

## Testing

1. **Desktop**: Run `python -m src.desktop.simple_app`
2. **Web**: Run `uvicorn src.web.main:app --reload`
3. Test Google Drive integration with the "Load Drive" and "Store Drive" buttons

## Troubleshooting

### "Access blocked" errors
- Add test users in Google Cloud Console → OAuth consent screen
- Or use personal Google account that owns the project

### "Invalid client" errors  
- Verify client IDs and secrets are correct in `.env`
- Check that redirect URIs match in Google Cloud Console

### "Picker not loading"
- Verify the Picker App ID is the correct project number
- Check browser console for JavaScript errors
