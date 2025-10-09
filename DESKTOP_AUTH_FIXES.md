# Desktop Authentication Fixes

## Issues Fixed

### 1. OAuth Client Secret Exposure (Security Issue)

**Problem:** The `google_client_secret` was being exposed to all clients (web and desktop) in the HTML template.

**Fix:** Modified `src/web/main.py` to only expose `google_client_secret` when `is_desktop` is True.

- Desktop detection now includes `?desktop=true` query parameter
- Web clients no longer receive the client secret

### 2. OAuth Poll Status Check (Bug)

**Problem:** The desktop loopback OAuth flow was checking for `pollData.status === 'complete'` but the backend returns `status === 'ok'`.

**Fix:** Updated `src/web/templates/index.html` line 2090 to check for `status === 'ok'` instead of `'complete'`.

### 3. Removed Insecure Test Files

**Deleted:**

- `test_page.html` - contained hardcoded OAuth credentials
- `tmp_index.html` - contained hardcoded OAuth credentials and duplicate auth code

## Desktop OAuth Flow

The desktop app now uses TWO OAuth methods:

### Method 1: Device Code Flow (Primary for Sync)

- User clicks "Sync Drive" button
- `authenticateGoogleDrive()` → `deviceFlowAuth()`
- Opens browser to Google's device authorization page
- User enters code and authorizes
- App polls Google for access token
- Token is saved to localStorage and sent to backend (Redis)

### Method 2: Loopback Flow (for Load/Store Drive)

- User clicks "Load Drive" or "Store Drive"
- `openDrivePickerAndImport()` or `storeDriveWithAuth()`
- Opens browser to Google OAuth with `redirect_uri=http://localhost:{port}/oauth/callback`
- User authorizes, Google redirects to `/oauth/callback`
- Backend stores auth code by state
- Frontend polls `/oauth/poll?state={state}`
- When status=='ok' and code is present, exchanges code for token
- Token saved to localStorage and backend

## Files Modified

1. `src/web/main.py`

   - Added detection of `?desktop=true` query parameter
   - Restricted `google_client_secret` to desktop only

2. `src/web/templates/index.html`

   - Fixed OAuth poll status check (complete → ok)
   - Removed deprecated OOB OAuth function

3. Deleted: `test_page.html`, `tmp_index.html`

## Testing Checklist

### Desktop App Launch

- [x] Run `python -m src.desktop.simple_app`
- [ ] Verify app opens in webview
- [ ] Verify databases list appears
- [ ] Verify "Load Drive" button exists
- [ ] Verify database cards have "Sync Drive" and "Store Drive" buttons

### OAuth Flows

#### Sync Drive (Device Code Flow)

- [ ] Click "Sync Drive" on a database
- [ ] Verify alert appears with verification URL and code
- [ ] Verify browser opens to Google verification page
- [ ] Enter code and authorize
- [ ] Verify success toast appears
- [ ] Verify button changes to "Unsync Drive"

#### Load Drive (Loopback Flow)

- [ ] Click "Load Drive" button
- [ ] Verify browser opens to Google OAuth consent
- [ ] Authorize application
- [ ] Verify redirect to /oauth/callback
- [ ] Verify Google Drive picker or file list appears
- [ ] Select a file and import

#### Store Drive (Loopback Flow)

- [ ] Click "Store Drive" on a database
- [ ] Verify browser opens to Google OAuth consent (if not already authorized)
- [ ] Authorize application
- [ ] Verify upload success toast

## Known Issues / Notes

1. **Empty Databases**: The desktop app starts with an empty `desktop.json` database. This is normal for a fresh install. Users can:

   - Create tables in the UI
   - Load databases from Drive
   - Import database JSON files

2. **OAuth Client Type**: The OAuth client must be configured as "Desktop app" in Google Cloud Console for device code flow to work. Web client type can be used for loopback flow.

3. **Port Detection**: Desktop app uses ports 8001-8099 (avoids 8000 reserved for web). The OAuth callback uses `window.location.origin` which should work with any port.

4. **Token Storage**:
   - Access tokens stored in: localStorage + backend Redis (for Celery sync)
   - Refresh tokens stored in: localStorage only
   - Tokens cleared on backend shutdown (see lifespan.py)

## Debugging

If OAuth doesn't prompt:

1. **Check browser console** (F12 in webview or external browser)

   - Look for "OAuth Config:" log with clientId
   - Check for errors in deviceFlowAuth() or performDesktopAuthSystemBrowser()

2. **Verify client_secret files exist**:

   ```bash
   ls secrets/client_secret_*.json
   ```

3. **Check if clientSecret is being passed to template**:

   - Open browser dev tools
   - In console, type: `console.log("{{ google_client_secret or 'MISSING' }}")`
   - Should show the client secret for desktop, empty for web

4. **Verify ?desktop=true is in URL**:

   - Check browser address bar or webview URL
   - Should be: `http://127.0.0.1:8001?desktop=true` (or similar port)

5. **Test OAuth endpoints directly**:
   ```bash
   curl http://localhost:8001/api/google/oauth/status
   # Should return: {"configured": true, "authenticated": false}
   ```

