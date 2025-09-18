# Complete Google Secrets Guide for TDMS

## Your Current Secrets in `/secrets` Folder

You have 3 different credential files, each for a different purpose:

### 1. **Desktop OAuth Client** ✅ CORRECTLY USED

- **File**: `client_secret_959795459883-0v78hklcovr3eldnsam4gkhgu0rbuj6i.apps.googleusercontent.com.json`
- **Type**: "installed" (Desktop application)
- **Client ID**: `959795459883-0v78hklcovr3eldnsam4gkhgu0rbuj6i.apps.googleusercontent.com`
- **Used for**: Desktop app authentication
- **Status**: ✅ Working correctly

### 2. **Web OAuth Client** ✅ CORRECTLY USED

- **File**: `client_secret_959795459883-p9maleogm01gsns6mi1uqnnigqo7e5ee.apps.googleusercontent.com.json`
- **Type**: "web" (Web application)
- **Client ID**: `959795459883-p9maleogm01gsns6mi1uqnnigqo7e5ee.apps.googleusercontent.com`
- **Used for**: Web app authentication (http://localhost:8000)
- **Status**: ✅ Working correctly

### 3. **Service Account** (OPTIONAL - NOT CURRENTLY USED)

- **File**: `fit-idiom-462507-p7-36977d98d2cc.json`
- **Type**: Service account
- **Client ID**: `118051022148118347635` ← This is NOT the Picker App ID!
- **Used for**: Server-side operations without user interaction
- **Status**: Available but not needed for current functionality

## What Goes in `.env` File

Here's exactly what you need in your `.env` file:

```env
# Desktop OAuth credentials (from installed app type)
DESKTOP_GOOGLE_OAUTH_CLIENT_ID=959795459883-0v78hklcovr3eldnsam4gkhgu0rbuj6i.apps.googleusercontent.com
DESKTOP_GOOGLE_OAUTH_CLIENT_SECRET=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

# Web OAuth credentials (from web app type)
GOOGLE_OAUTH_CLIENT_ID=959795459883-p9maleogm01gsns6mi1uqnnigqo7e5ee.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=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

# Google Picker App ID (IMPORTANT - see below)
GOOGLE_PICKER_APP_ID=959795459883

# Google API Key (OPTIONAL - only if you have one)
GOOGLE_API_KEY=

# Service Account (OPTIONAL - not needed for current setup)
# GOOGLE_SERVICE_ACCOUNT_FILE=fit-idiom-462507-p7-36977d98d2cc.json
```

## About Google Picker App ID

The **Picker App ID** is NOT the service account client ID (118051022148118347635).

The correct **Picker App ID** is: `959795459883`

This is derived from your OAuth client IDs:

- Look at your client ID: `959795459883-xxxxx.apps.googleusercontent.com`
- The Picker App ID is the first part: `959795459883`

## Where to Find These Values in Google Cloud Console

1. **Go to**: https://console.cloud.google.com/
2. **Select your project**: `fit-idiom-462507-p7`
3. **Navigate to**: APIs & Services → Credentials

You'll see:

- **OAuth 2.0 Client IDs**: Your web and desktop clients
- **Service accounts**: Your service account
- **API Keys**: If you've created any

### To Get Google API Key (Optional):

1. Click "Create Credentials" → "API Key"
2. Restrict it to Google Drive API
3. Add to `.env` as `GOOGLE_API_KEY=your_key_here`

## Current Status

✅ **Desktop App**: Uses correct desktop OAuth client from secrets folder
✅ **Web App**: Uses correct web OAuth client from secrets folder
✅ **Picker App ID**: Correctly set to `959795459883`
❌ **Google API Key**: Not set (optional, not required for basic functionality)
⚠️ **Service Account**: Available but not used (not needed for current setup)

## The Authentication Problem & Solution

The issue you're facing with "Access blocked" is because:

1. Google requires app verification for public apps
2. Verification can take weeks and requires extensive documentation

**Solution**: Run `setup_google_auth.bat` to generate a personal refresh token that bypasses all verification requirements.

## Summary

Your secrets are **correctly configured**! The app is using:

- Desktop client for desktop app ✅
- Web client for web app ✅
- Correct Picker App ID ✅

The only issue is Google's verification requirement, which is solved by running `setup_google_auth.bat` to generate a personal token.
