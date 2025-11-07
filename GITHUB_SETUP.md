# GitHub Repository Setup Guide

This guide will walk you through setting up the GitHub repository and configuring GitHub Actions for the employee profile sync automation.

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the **"+"** icon (top right) → **"New repository"**
3. Configure repository:
   - **Repository name**: `employee-profile-sync` (or your preferred name)
   - **Description**: "Automated sync of employee profiles from Finance Public data"
   - **Visibility**: Select **"Private"** (recommended for security)
   - **Initialize**: Don't check "Add a README" (we'll add files manually)
   - Click **"Create repository"**

## Step 2: Upload Files to Repository

### Option A: Using GitHub Web Interface

1. In your new repository, click **"uploading an existing file"**
2. Upload these files from `github-version/` folder:
   - `sync_employee_profiles.py`
   - `requirements.txt`
   - `.gitignore`
   - `README.md`
   - `DROPBOX_SETUP.md`
   - `GITHUB_SETUP.md`
3. For `.github/workflows/sync-employee-profiles.yml`:
   - Click **"Add file"** → **"Create new file"**
   - Path: `.github/workflows/sync-employee-profiles.yml`
   - Paste the workflow content
4. Click **"Commit changes"** → **"Commit directly to the main branch"**

### Option B: Using Git Command Line

```bash
# Navigate to github-version folder
cd /Users/nikolay/Library/CloudStorage/Dropbox/Nov25/.automation/github-version

# Initialize git repository
git init

# Add all files
git add .

# Commit files
git commit -m "Initial commit: Employee profile sync automation"

# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/employee-profile-sync.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Add Dropbox Access Token Secret

1. In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Configure secret:
   - **Name**: `DROPBOX_ACCESS_TOKEN` (must match exactly)
   - **Value**: Paste your Dropbox access token from [DROPBOX_SETUP.md](DROPBOX_SETUP.md)
   - Click **"Add secret"**

**Important**: The secret name must be exactly `DROPBOX_ACCESS_TOKEN` (case-sensitive).

## Step 4: Test Workflow Manually

1. Go to **Actions** tab in your repository
2. You should see **"Employee Profile Sync"** workflow
3. Click on it, then click **"Run workflow"** button (right side)
4. Select branch: **main**
5. Click **"Run workflow"**
6. Watch the workflow execute:
   - Click on the running workflow
   - Expand each step to see logs
   - Wait for completion (takes 2-4 minutes)

## Step 5: Verify Results

### Check Workflow Logs
1. In Actions tab, click on the completed workflow run
2. Expand **"Run employee profile sync"** step
3. Look for:
   - ✅ "Connected to Dropbox account: [your email]"
   - ✅ "Parsed 70 employees from Finance file"
   - ✅ "Found 43 profile files"
   - ✅ "Profiles Updated: [number]"
   - ✅ "Sync Complete"

### Check Artifacts
1. Scroll to bottom of workflow run page
2. Under **"Artifacts"**, download `sync-logs-[number]`
3. Extract and check:
   - `sync.log` - Full execution log
   - `last_sync.json` - Sync statistics and changes

### Verify Dropbox Files
1. Check your Dropbox files were updated
2. Open a few profile files to verify changes
3. Compare with Finance Public data

## Step 6: Monitor Scheduled Runs

The workflow is configured to run daily at **8:00 AM UTC**.

### Check Schedule
- Go to **Actions** tab → **"Employee Profile Sync"** workflow
- Click **"..."** (three dots) → **"View workflow file"**
- Verify cron schedule: `'0 8 * * *'`

### Timezone Note
- GitHub Actions uses UTC time
- 8:00 AM UTC = different local times:
  - EST (UTC-5): 3:00 AM
  - PST (UTC-8): 12:00 AM (midnight)
  - CET (UTC+1): 9:00 AM

To change the schedule, edit `.github/workflows/sync-employee-profiles.yml` and update the cron expression.

### Monitor Execution
- Check **Actions** tab daily to verify runs
- Review logs if any failures occur
- Download artifacts to track changes over time

## Troubleshooting

### Workflow doesn't appear in Actions tab
- Verify `.github/workflows/sync-employee-profiles.yml` exists
- Check file is in correct location
- Ensure YAML syntax is valid

### "Secret not found" error
- Verify secret name is exactly `DROPBOX_ACCESS_TOKEN`
- Check secret exists in Settings → Secrets and variables → Actions
- Re-add secret if needed

### Workflow fails with "Invalid Dropbox access token"
- Verify token is correct in GitHub Secrets
- Check token hasn't expired (regenerate if needed)
- Test token locally first (see DROPBOX_SETUP.md)

### Workflow doesn't run on schedule
- GitHub Actions can have up to 10-minute delay
- Verify cron syntax is correct (use [crontab.guru](https://crontab.guru))
- Check Actions are enabled: Settings → Actions → General

### No artifacts uploaded
- Artifacts only upload if workflow completes (even with errors)
- Check if `sync.log` and `last_sync.json` are generated
- Verify file paths in workflow match script output

## Manual Workflow Trigger

You can manually trigger the workflow anytime:

1. Go to **Actions** tab
2. Select **"Employee Profile Sync"** workflow
3. Click **"Run workflow"** → **"Run workflow"**

This is useful for:
- Testing after setup
- Running sync outside scheduled time
- Debugging issues

## Next Steps

After successful setup:
1. ✅ Monitor first scheduled run (next day at 8 AM UTC)
2. ✅ Review logs and artifacts
3. ✅ Verify Dropbox files are updated correctly
4. ✅ Set up notifications (optional - see README.md)

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

