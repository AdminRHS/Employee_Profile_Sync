# Dropbox App Setup Guide

This guide will walk you through creating a Dropbox App and generating an access token for the employee profile sync automation.

## Step 1: Create Dropbox App

1. Go to [Dropbox Developers Console](https://www.dropbox.com/developers/apps)
2. Click **"Create App"** button (top right)
3. Configure your app:
   - **Choose an API**: Select **"Scoped access"**
   - **Choose the type of access you need**: Select **"Full Dropbox"**
   - **Name your app**: Enter `employee-profile-sync` (or your preferred name)
   - Click **"Create App"**

## Step 2: Configure Permissions

1. In your app dashboard, go to the **"Permissions"** tab
2. Enable the following scopes:
   - ✅ **files.metadata.read** - List and view file metadata
   - ✅ **files.content.read** - Download file content
   - ✅ **files.content.write** - Upload or modify files
3. Click **"Submit"** to save permissions

## Step 3: Generate Access Token

1. Go to the **"Settings"** tab in your app dashboard
2. Scroll down to **"OAuth 2"** section
3. Under **"Generated access token"**, click **"Generate"**
4. **IMPORTANT**: Copy the token immediately (it starts with `sl.`)
   - The token will be shown only once
   - If you lose it, you'll need to generate a new one
5. Save the token securely - you'll need it for GitHub Secrets

## Step 4: Security Best Practices

### Token Security
- ✅ **Never commit the token to GitHub** - Always use GitHub Secrets
- ✅ **Keep the token private** - Don't share it in emails or messages
- ✅ **Rotate periodically** - Generate a new token every 6-12 months
- ✅ **Revoke old tokens** - Delete unused tokens from app settings

### App Settings
- ✅ **Keep app private** - Don't share app access with others
- ✅ **Monitor app activity** - Check Dropbox dashboard for unusual activity
- ✅ **Use scoped access** - Only request permissions you need

## Step 5: Verify Token Works

You can test your token locally before adding it to GitHub:

```bash
# Install Dropbox SDK
pip install dropbox

# Test connection (replace YOUR_TOKEN with your actual token)
python3 -c "
import dropbox
dbx = dropbox.Dropbox('YOUR_TOKEN')
account = dbx.users_get_current_account()
print(f'Connected as: {account.email}')
"
```

If successful, you'll see your Dropbox email address.

## Troubleshooting

### "Invalid access token" error
- Verify token was copied correctly (no extra spaces)
- Check if token was revoked in Dropbox app settings
- Generate a new token if needed

### "Insufficient permissions" error
- Verify all required scopes are enabled in Permissions tab
- Regenerate token after enabling permissions

### Token not working in GitHub Actions
- Double-check token is correctly added to GitHub Secrets
- Verify secret name matches: `DROPBOX_ACCESS_TOKEN`
- Check GitHub Actions logs for specific error messages

## Next Steps

After completing this setup:
1. Copy your access token
2. Follow [GITHUB_SETUP.md](GITHUB_SETUP.md) to add it to GitHub Secrets
3. Test the workflow manually in GitHub Actions

## Additional Resources

- [Dropbox API Documentation](https://www.dropbox.com/developers/documentation)
- [Dropbox OAuth Guide](https://www.dropbox.com/developers/reference/oauth-guide)
- [Dropbox Python SDK](https://github.com/dropbox/dropbox-sdk-python)

