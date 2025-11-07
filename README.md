# Employee Profile Sync Automation

Automated synchronization of employee profiles from Finance Public data to department profile files using GitHub Actions and Dropbox API.

## Overview

This automation system keeps employee profile files up-to-date by syncing data from the Finance Public markdown file to individual employee profile files across all departments.

**Source**: `/Finance Public/November 2025 - Employees_Public.md`  
**Targets**: `/Nov25/[Department]/[Employee Name]/Profile*.md`  
**Synced Fields**: ID, Rate, Status, Profession

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

## Features

- ✅ **24/7 Automation** - Runs in cloud, no laptop dependency
- ✅ **Free** - Uses GitHub Actions free tier (2,000 min/month)
- ✅ **Reliable** - GitHub's infrastructure, not dependent on local machine
- ✅ **Monitored** - Complete logs and artifacts for every run
- ✅ **Safe** - Dry-run mode for testing, preserves all other profile content
- ✅ **Flexible** - Manual trigger available anytime

## Migration Status

**Previous System**: Laptop-based launchd scheduler  
**Current System**: GitHub Actions cloud automation  
**Status**: ✅ Migrated - Runs independently of laptop status

## Quick Start

### Prerequisites

- GitHub account (free)
- Dropbox account with Developer access
- Python 3.11+ (for local testing only)

### Setup Steps

1. **Create Dropbox App** - Follow [DROPBOX_SETUP.md](DROPBOX_SETUP.md)
2. **Create GitHub Repository** - Follow [GITHUB_SETUP.md](GITHUB_SETUP.md)
3. **Add Dropbox Token** - Add to GitHub Secrets as `DROPBOX_ACCESS_TOKEN`
4. **Test Workflow** - Run manually via GitHub Actions UI
5. **Monitor** - Check Actions tab for scheduled runs

## File Structure

```
github-version/
├── .github/
│   └── workflows/
│       └── sync-employee-profiles.yml    # GitHub Actions workflow
├── sync_employee_profiles.py             # Main sync script
├── requirements.txt                       # Python dependencies
├── .gitignore                            # Git ignore rules
├── README.md                              # This file
├── DROPBOX_SETUP.md                      # Dropbox App setup guide
└── GITHUB_SETUP.md                       # GitHub repository setup guide
```

## How It Works

### Sync Process

1. **Trigger**: GitHub Actions runs daily at 8:00 AM UTC (or manually)
2. **Connect**: Script connects to Dropbox using access token
3. **Download**: Downloads Finance Public markdown file
4. **Parse**: Extracts employee data (ID, Name, Status, Rate, Profession)
5. **Find**: Locates all Profile*.md files in /Nov25 directory
6. **Match**: Matches profile files to Finance data by employee name
7. **Update**: Updates 4 fields: ID, Rate, Status, Profession
8. **Upload**: Uploads modified files back to Dropbox
9. **Log**: Generates logs and artifacts for monitoring

### Matching Logic

- Primary: Direct name match
- Fallback: Case-insensitive match
- Fallback: Last name + first name match

### Fields Updated

- **ID**: Employee ID number
- **Rate**: Hourly/daily rate
- **Status**: Work status (Work, Project, Available, etc.)
- **Profession**: Job title/profession

All other profile content (skills, tools, summaries) is preserved unchanged.

## Schedule

**Default**: Daily at 8:00 AM UTC

To change schedule, edit `.github/workflows/sync-employee-profiles.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'  # Change this cron expression
```

Use [crontab.guru](https://crontab.guru) to create custom schedules.

## Monitoring

### GitHub Actions Dashboard

- **Location**: Repository → Actions tab
- **Shows**: All workflow runs, success/failure status, execution time
- **Logs**: Detailed logs for each step
- **Artifacts**: Download sync logs and state files

### Artifacts

Each run generates:
- `sync.log` - Complete execution log
- `last_sync.json` - Sync statistics and change history

### Key Metrics

- Profiles Found: Total profile files discovered
- Profiles Updated: Files that had changes
- Profiles Skipped: Files without matching Finance data
- Fields Changed: Total number of field updates
- Errors: Any errors encountered

## Local Testing

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

## Troubleshooting

### Common Issues

**Workflow doesn't run on schedule**
- GitHub Actions can have up to 10-minute delay
- Verify cron syntax is correct
- Check Actions are enabled in repository settings

**"Invalid Dropbox access token" error**
- Verify token in GitHub Secrets
- Check token hasn't expired
- Regenerate token if needed

**"File not found" error**
- Verify Finance file path: `/Finance Public/November 2025 - Employees_Public.md`
- Check Dropbox app has Full Dropbox access
- Verify file exists in your Dropbox

**No profiles found**
- Verify /Nov25 directory exists in Dropbox
- Check Profile*.md files exist
- Review script logs for specific errors

**Profiles not updating**
- Check if employee names match between Finance file and profile folders
- Review matching logic in logs
- Verify Finance file has correct data

### Getting Help

1. Check workflow logs in GitHub Actions
2. Review artifacts for detailed error messages
3. Test locally with dry-run mode
4. Verify Dropbox token and permissions

## Security

### Token Security
- ✅ Token stored in GitHub Secrets (encrypted)
- ✅ Never committed to repository
- ✅ Only accessible during workflow execution

### Repository Security
- ✅ Private repository recommended
- ✅ No sensitive data in code
- ✅ All paths use environment variables

### Dropbox Security
- ✅ Scoped access (only required permissions)
- ✅ Token rotation recommended every 6-12 months
- ✅ Monitor app activity in Dropbox dashboard

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

## Rollback Plan

If GitHub Actions fails, you can restore laptop-based automation:

1. Restore launchd plist from backup
2. Load scheduler: `launchctl load ~/Library/LaunchAgents/com.user.employee-sync.plist`
3. Test manually: Run sync script locally

## Future Enhancements

Potential improvements:
- Slack/Email notifications on failures
- Incremental sync (only changed files)
- Conflict detection (warn before overwriting)
- HTML reports with sync statistics
- Multi-source sync support

## Contributing

This is a private automation system. For changes:
1. Test locally first with dry-run mode
2. Test manually in GitHub Actions
3. Monitor first scheduled run
4. Review logs and artifacts

## License

Private automation system - Internal use only.

## Support

For issues or questions:
1. Review troubleshooting section
2. Check GitHub Actions logs
3. Test locally with dry-run mode
4. Verify Dropbox and GitHub setup

---

**Last Updated**: November 2025  
**Status**: ✅ Active - Running daily at 8:00 AM UTC  
**Version**: 2.0 (GitHub Actions)

