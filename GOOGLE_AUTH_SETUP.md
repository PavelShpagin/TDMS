# Google Drive OAuth Setup Guide

## The Problem

Google blocks OAuth access for unverified apps to protect users. Since verification can take weeks and requires extensive documentation, here are alternative solutions:

## Solution 1: Personal Use Token (Recommended for Desktop)

This approach uses YOUR personal Google account to create a long-lived refresh token that the app can use.

### Steps:

1. **Create Your Own OAuth Client**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Drive API
   - Go to "Credentials" → "Create Credentials" → "OAuth Client ID"
   - Choose "Desktop app" type
   - Download the JSON file

2. **Generate Personal Refresh Token**

   - Run the setup script below to generate a refresh token
   - This token can be used indefinitely (unless revoked)

3. **Use the Token in the App**
   - The app will use this refresh token to access Google Drive
   - No repeated authorization needed

## Solution 2: Use Google Colab / Jupyter Approach

Instead of traditional OAuth, use a simpler token-based approach:

1. User generates token in Google Colab/Jupyter
2. Pastes token into the app
3. App uses token for API access

## Solution 3: Service Account (For Your Files Only)

Use a service account to access a specific Google Drive folder:

1. Create service account in Google Cloud Console
2. Share specific folders with the service account email
3. App uses service account to access those folders

## Implementation

I'll implement Solution 1 with a setup script that generates a permanent refresh token.
