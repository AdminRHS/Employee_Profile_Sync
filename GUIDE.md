# Employee Profile Sync Automation - Complete Guide

Automated synchronization of employee profiles from Finance Public data to department profile files using GitHub Actions and Dropbox API.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Initial Setup](#initial-setup)
4. [Troubleshooting](#troubleshooting)
5. [Monitoring & Usage](#monitoring--usage)
6. [Security](#security)

---

## Overview

**Source**: `/Finance Public/November 2025 - Employees_Public.md`  
**Targets**: `/Nov25/[Department]/[Employee Name]/Profile*.md`  
**Synced Fields**: ID, Rate, Status, Profession

### Features

- ✅ **24/7 Automation** - Runs in cloud, no laptop dependency
- ✅ **Free** - Uses GitHub Actions free tier (2,000 min/month)
- ✅ **Reliable** - GitHub's infrastructure, not dependent on local machine
- ✅ **Monitored** - Complete logs and artifacts for every run
- ✅ **Safe** - Dry-run mode for testing, preserves all other profile content
- ✅ **Flexible** - Manual trigger available anytime

### Status

**Current System**: GitHub Actions cloud automation  
**Status**: ✅ Active - Running daily at 8:00 AM UTC  
**Repository**: https://github.com/AdminRHS/Employee_Profile_Sync

---

## Architecture

```
GitHub Actions (Cloud)
    ↓
    Runs daily at 8:00 AM UTC
    ↓
Python Script (sync_employee_profiles.py)
    ↓
Dropbox API
    ↓
Downloads Finance file
    ↓
Finds all Profile*.md files
    ↓
Updates fields (ID, Rate, Status, Profession)
    ↓
Uploads modified files back to Dropbox
```

### How It Works

1. **Trigger**: GitHub Actions runs daily at 8:00 AM UTC (or manually)
2. **Connect**: Script connects to Dropbox using access token
3. **Download**: Downloads Finance Public markdown file
4. **Parse**: Extracts employee data (ID, Name, Status, Rate, Profession)
5. **Find**: Locates all Profile*.md files in /Nov25 directory
6. **Match**: Matches profile files to Finance data by employee name
7. **Update**: Updates 4 fields: ID, Rate, Status, Profession
8. **Upload**: Uploads modified files back to Dropbox
9. **Log**: Generates logs and artifacts for monitoring

---

## Initial Setup

### Prerequisites

- GitHub account (free)
- Dropbox account with Developer access
- Python 3.11+ (for local testing only)

### Step 1: Create Dropbox App

1. Go to [Dropbox Developers Console](https://www.dropbox.com/developers/apps)
2. Click **"Create App"** button (top right)
3. Configure your app:
   - **Choose an API**: Select **"Scoped access"**
   - **Choose the type of access you need**: Select **"Full Dropbox"**
   - **Name your app**: Enter `employee-profile-sync` (or your preferred name)
   - Click **"Create App"**

### Step 2: Configure Dropbox Permissions

1. In your app dashboard, go to the **"Permissions"** tab
2. Enable the following scopes:
   - ✅ **files.metadata.read** - List and view file metadata
   - ✅ **files.content.read** - Download file content
   - ✅ **files.content.write** - Upload or modify files
3. Click **"Submit"** to save permissions

### Step 3: Generate Dropbox Access Token

1. Go to the **"Settings"** tab in your app dashboard
2. Scroll down to **"OAuth 2"** section
3. Under **"Generated access token"**, click **"Generate"**
4. **IMPORTANT**: Copy the token immediately (it starts with `sl.`)
   - The token will be shown only once
   - If you lose it, you'll need to generate a new one
5. Save the token securely - you'll need it for GitHub Secrets

### Step 4: Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the **"+"** icon (top right) → **"New repository"**
3. Configure repository:
   - **Repository name**: `employee-profile-sync` (or your preferred name)
   - **Description**: "Automated sync of employee profiles from Finance Public data"
   - **Visibility**: Select **"Private"** (recommended for security)
   - **Initialize**: Don't check "Add a README"
   - Click **"Create repository"**

### Step 5: Push Files to GitHub

Files are already in the `github-version/` folder. Push them:

```bash
cd "/Users/nikolay/Library/CloudStorage/Dropbox/Nov25/.automation/github-version"
git push -u origin main
```

You'll need a GitHub Personal Access Token:
1. Go to: https://github.com/settings/tokens
2. Generate new token (classic) with `repo` scope
3. Use token as password when pushing

### Step 6: Add Dropbox Token to GitHub Secrets

1. Go to: https://github.com/AdminRHS/Employee_Profile_Sync/settings/secrets/actions
2. Click **"New repository secret"**
3. Configure:
   - **Name**: `DROPBOX_ACCESS_TOKEN` (must match exactly, case-sensitive)
   - **Value**: Paste your Dropbox access token
   - Click **"Add secret"**

### Step 7: Test Workflow

1. Go to: https://github.com/AdminRHS/Employee_Profile_Sync/actions
2. Click **"Employee Profile Sync"** workflow
3. Click **"Run workflow"** → **"Run workflow"**
4. Monitor execution and verify success

---

## Troubleshooting

### Invalid Dropbox Token Error

**Error**: `Invalid authorization value in HTTP header "Authorization"`

**Solution**:
1. Delete the secret in GitHub: Settings → Secrets → Actions → Delete `DROPBOX_ACCESS_TOKEN`
2. Re-add the secret carefully:
   - Name: `DROPBOX_ACCESS_TOKEN` (exact match)
   - Value: Copy token EXACTLY (no spaces before/after, no line breaks)
   - Token starts with `sl.u.` and is very long
3. Test again

**Common Mistakes**:
- ❌ Adding spaces before/after the token
- ❌ Missing characters at the beginning or end
- ❌ Wrong secret name (must be exactly `DROPBOX_ACCESS_TOKEN`)
- ❌ Copying only part of the token

### Missing Permissions Error

**Error**: `Your app is not permitted to access this endpoint because it does not have the required scope 'files.content.read'`

**Solution**:
1. Go to Dropbox App Console: https://www.dropbox.com/developers/apps
2. Click on your app → **"Permissions"** tab
3. Enable all required scopes:
   - ✅ files.metadata.read
   - ✅ files.content.read
   - ✅ files.content.write
4. Click **"Submit"**
5. **IMPORTANT**: Regenerate access token (old tokens don't get new permissions)
   - Go to **"Settings"** tab → **"OAuth 2"** → **"Generate"** new token
6. Update GitHub Secret with the new token

### Workflow Doesn't Run on Schedule

**Possible Causes**:
- GitHub Actions can have up to 10-minute delay
- Cron syntax might be incorrect
- Actions might be disabled

**Solution**:
1. Verify cron syntax: `'0 8 * * *'` (use [crontab.guru](https://crontab.guru))
2. Check Actions are enabled: Settings → Actions → General
3. Wait up to 10 minutes after scheduled time

### File Not Found Error

**Error**: `Finance file not found`

**Solution**:
1. Verify Finance file path: `/Finance Public/November 2025 - Employees_Public.md`
2. Check Dropbox app has Full Dropbox access
3. Verify file exists in your Dropbox

### No Profiles Found

**Solution**:
1. Verify /Nov25 directory exists in Dropbox
2. Check Profile*.md files exist
3. Review script logs for specific errors

### Profiles Not Updating

**Solution**:
1. Check if employee names match between Finance file and profile folders
2. Review matching logic in logs
3. Verify Finance file has correct data

### Profile Matching Warnings

Sometimes profiles are skipped with warnings. Common reasons:

**1. Name Mismatch**
- **Problem**: Folder name doesn't match Finance file name exactly
- **Example**: Folder `Safonova Elleonora` vs Finance `Safonova Eleonora`
- **Solution**: Rename folder to match Finance file exactly

**2. Employee Not in Finance File**
- **Problem**: Profile exists but employee not listed in Finance file
- **Example**: Employees in `Left` folder
- **Solution**: This is expected - inactive employees won't sync

**3. Character Encoding Issues**
- **Problem**: Special characters in names don't match
- **Example**: `Azanova Darya` vs `Azanova Darʼya` (special apostrophe)
- **Solution**: Rename folder to match Finance file exactly (including special characters)

**How to Fix Name Mismatches:**
1. Check Finance file for exact name spelling
2. Rename employee folder to match exactly
3. Rename profile file if needed
4. Next sync will find and update the profile

---

## Monitoring & Usage

### Schedule

**Default**: Daily at 8:00 AM UTC

**Timezone Conversion**:
- EST (UTC-5): 3:00 AM
- PST (UTC-8): 12:00 AM (midnight)
- CET (UTC+1): 9:00 AM

**Change Schedule**: Edit `.github/workflows/sync-employee-profiles.yml`:
```yaml
schedule:
  - cron: '0 8 * * *'  # Change this cron expression
```

### Manual Trigger

You can manually trigger the workflow anytime:
1. Go to: https://github.com/AdminRHS/Employee_Profile_Sync/actions
2. Click **"Run workflow"** → **"Run workflow"**

### Monitoring

**GitHub Actions Dashboard**:
- Location: Repository → Actions tab
- Shows: All workflow runs, success/failure status, execution time
- Logs: Detailed logs for each step
- Artifacts: Download sync logs and state files

**Artifacts** (downloaded after each run):
- `sync.log` - Complete execution log
- `last_sync.json` - Sync statistics and change history

**Key Metrics**:
- Profiles Found: Total profile files discovered
- Profiles Updated: Files that had changes
- Profiles Skipped: Files without matching Finance data
- Fields Changed: Total number of field updates
- Errors: Any errors encountered

### Local Testing

Test the script locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Set Dropbox token
export DROPBOX_ACCESS_TOKEN="your_token_here"

# Dry run (no changes)
python sync_employee_profiles.py --dry-run

# Actual run
python sync_employee_profiles.py
```

---

## Security

### Token Security

- ✅ Token stored in GitHub Secrets (encrypted)
- ✅ Never committed to repository
- ✅ Only accessible during workflow execution
- ✅ Rotate token every 6-12 months

### Repository Security

- ✅ Private repository recommended
- ✅ No sensitive data in code
- ✅ All paths use environment variables

### Dropbox Security

- ✅ Scoped access (only required permissions)
- ✅ Monitor app activity in Dropbox dashboard
- ✅ Keep app private (don't share access)

---

## File Structure

```
.github/
└── workflows/
    └── sync-employee-profiles.yml    # GitHub Actions workflow
sync_employee_profiles.py             # Main sync script
requirements.txt                       # Python dependencies
.gitignore                            # Git ignore rules
GUIDE.md                              # This file (complete guide)
```

---

## Cost Analysis

### GitHub Actions
- **Free Tier**: 2,000 minutes/month for private repos
- **Usage**: ~4 minutes per run × 30 runs/month = ~120 minutes
- **Percentage**: 6% of free tier
- **Cost**: $0 (well within free limits)

### Dropbox API
- **Free Tier**: Unlimited API calls for basic tier
- **Storage**: Files are tiny (<1 MB total)
- **Cost**: $0

---

## Support

For issues or questions:
1. Review troubleshooting section above
2. Check GitHub Actions logs
3. Test locally with dry-run mode
4. Verify Dropbox token and permissions

---

**Last Updated**: November 2025  
**Status**: ✅ Active - Running daily at 8:00 AM UTC  
**Version**: 2.0 (GitHub Actions)

