# How to Add Test Users in Google Cloud Console

## Step-by-Step Instructions

### 1. Go to Google Cloud Console

- Visit: https://console.cloud.google.com/
- Select your project: `fit-idiom-462507-p7`

### 2. Navigate to OAuth Consent Screen

- In the left sidebar: **APIs & Services** → **OAuth consent screen**
- OR direct link: https://console.cloud.google.com/apis/credentials/consent

### 3. Check Your App Status

You should see one of these statuses:

- **Testing** - You can add test users
- **In production** - Need to submit for verification
- **Needs verification** - Need to submit for verification

### 4. Add Test Users (If in Testing Mode)

If your app shows "Testing" status:

1. **Scroll down to "Test users" section**
2. **Click "ADD USERS" button**
3. **Enter email addresses** (one per line):
   ```
   your.email@gmail.com
   another.email@gmail.com
   ```
4. **Click "SAVE"**

### 5. If You Don't See "Test Users" Section

Your app might be in production mode. To switch to testing:

1. **Click "EDIT APP" at the top**
2. **In "Publishing status"** - select **"Testing"**
3. **Click "SAVE AND CONTINUE"**
4. **Now you should see "Test users" section**

### 6. Important Notes

- **Test users limit**: Up to 100 test users
- **No verification needed**: Test users can use the app immediately
- **Sensitive scopes**: Even test users need to go through consent for sensitive scopes
- **Domain restriction**: If using Google Workspace, you can restrict to your domain

### 7. Alternative: Use Internal User Type

If you're part of a Google Workspace organization:

1. **In OAuth consent screen setup**
2. **Choose "Internal" user type** instead of "External"
3. **This allows all users in your organization** without adding them individually
4. **No verification required** for internal apps

### 8. Troubleshooting

**Can't find "Test users" section?**

- Make sure app is in "Testing" status
- Try refreshing the page
- Check you're in the right project

**Still getting "Access blocked"?**

- Clear browser cookies/cache for Google accounts
- Try incognito/private browsing mode
- Make sure the email you're testing with is added as a test user

**"This app isn't verified" warning?**

- This is normal for test apps
- Click "Advanced" → "Go to [app name] (unsafe)"
- This allows you to proceed with testing
