#!/usr/bin/env python3
"""
Employee Profile Sync Automation - GitHub Actions Version
Syncs employee profiles from Finance Public data to department profile files via Dropbox API.

Source: /Finance Public/November 2025 - Employees_Public.md
Targets: /Nov25/[Department]/[Employee Name]/Profile*.md

Synced Fields: ID, Rate, Status, Profession
"""

import os
import re
import json
import sys
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import dropbox
    from dropbox.exceptions import ApiError, AuthError
except ImportError:
    print("ERROR: Dropbox SDK not installed. Run: pip install dropbox")
    sys.exit(1)


class EmployeeProfileSyncDropbox:
    def __init__(self, access_token: str, dry_run: bool = False, 
                 app_key: Optional[str] = None, app_secret: Optional[str] = None, 
                 refresh_token: Optional[str] = None):
        self.dry_run = dry_run
        self.app_key = app_key
        self.app_secret = app_secret
        self.refresh_token = refresh_token
        
        # Initialize Dropbox client with token refresh support
        self.dbx = self._init_dropbox_client(access_token)
        self.changes = []
        self.errors = []
        self.stats = {
            "profiles_found": 0,
            "profiles_updated": 0,
            "profiles_skipped": 0,
            "fields_changed": 0,
            "folders_created": 0,
            "profiles_created": 0
        }

    def _validate_refresh_credentials(self) -> Tuple[bool, List[str]]:
        """Check if refresh token setup is complete
        
        Returns:
            Tuple of (is_complete, missing_secrets)
        """
        missing = []
        if not self.app_key:
            missing.append("DROPBOX_APP_KEY")
        if not self.app_secret:
            missing.append("DROPBOX_APP_SECRET")
        if not self.refresh_token:
            missing.append("DROPBOX_REFRESH_TOKEN")
        
        return (len(missing) == 0, missing)
    
    def _init_dropbox_client(self, access_token: str) -> dropbox.Dropbox:
        """Initialize Dropbox client with automatic token refresh if refresh token is available"""
        try:
            # Note: Dropbox() constructor doesn't validate the token, so this won't fail here
            # Token validation happens on first API call, which is handled in run_sync()
            return dropbox.Dropbox(access_token)
        except Exception as e:
            # This catch is unlikely to trigger since Dropbox() constructor doesn't validate tokens
            # But keeping it for safety
            self.log(f"Unexpected error during Dropbox client initialization: {e}", "WARN")
            if self.refresh_token and self.app_key and self.app_secret:
                self.log("Refresh credentials available, attempting token refresh...", "INFO")
                new_token = self._refresh_access_token()
                if new_token:
                    return dropbox.Dropbox(new_token)
            raise e
    
    def _refresh_access_token(self) -> Optional[str]:
        """Refresh access token using refresh token"""
        is_complete, missing = self._validate_refresh_credentials()
        if not is_complete:
            self.log(f"Refresh token credentials incomplete. Missing: {', '.join(missing)}", "ERROR")
            return None
        
        self.log("Attempting to refresh access token...", "INFO")
        self.log(f"Using refresh token endpoint: https://api.dropbox.com/oauth2/token", "INFO")
        self.log(f"App key present: {'Yes' if self.app_key else 'No'} (length: {len(self.app_key) if self.app_key else 0})", "INFO")
        self.log(f"App secret present: {'Yes' if self.app_secret else 'No'} (length: {len(self.app_secret) if self.app_secret else 0})", "INFO")
        self.log(f"Refresh token present: {'Yes' if self.refresh_token else 'No'} (length: {len(self.refresh_token) if self.refresh_token else 0})", "INFO")
        
        try:
            url = "https://api.dropbox.com/oauth2/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            }
            auth = (self.app_key, self.app_secret)
            
            self.log("Sending refresh token request to Dropbox API...", "INFO")
            response = requests.post(url, data=data, auth=auth, timeout=30)
            
            self.log(f"Refresh API response status: {response.status_code}", "INFO")
            
            if response.status_code != 200:
                error_text = response.text[:200]  # Limit error text length
                self.log(f"Refresh API returned error status {response.status_code}: {error_text}", "ERROR")
                response.raise_for_status()
            
            result = response.json()
            
            # Log response details (without exposing tokens)
            if "access_token" in result:
                self.log("Refresh API response: access_token received (length: {})".format(len(result.get("access_token", ""))), "INFO")
            else:
                self.log(f"Refresh API response: No access_token in response. Keys: {list(result.keys())}", "ERROR")
            
            new_access_token = result.get("access_token")
            
            if new_access_token:
                self.log("✅ Successfully refreshed access token", "INFO")
                return new_access_token
            else:
                self.log("❌ Refresh response did not contain access_token", "ERROR")
                if "error" in result:
                    self.log(f"Refresh API error: {result.get('error')} - {result.get('error_description', 'No description')}", "ERROR")
                return None
                
        except requests.exceptions.HTTPError as e:
            error_text = str(e)
            if hasattr(e.response, 'text'):
                error_text = e.response.text[:200]
            self.log(f"HTTP error during token refresh: {error_text}", "ERROR")
            return None
        except requests.exceptions.RequestException as e:
            self.log(f"Request error during token refresh: {e}", "ERROR")
            return None
        except Exception as e:
            self.log(f"Unexpected error during token refresh: {type(e).__name__}: {e}", "ERROR")
            return None

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)

    def download_file(self, dropbox_path: str) -> Optional[str]:
        """Download file content from Dropbox"""
        try:
            metadata, response = self.dbx.files_download(dropbox_path)
            content = response.content.decode('utf-8')
            return content
        except ApiError as e:
            self.log(f"Error downloading {dropbox_path}: {e}", "ERROR")
            return None

    def upload_file(self, dropbox_path: str, content: str) -> bool:
        """Upload file content to Dropbox"""
        try:
            self.dbx.files_upload(
                content.encode('utf-8'),
                dropbox_path,
                mode=dropbox.files.WriteMode.overwrite
            )
            return True
        except ApiError as e:
            self.log(f"Error uploading {dropbox_path}: {e}", "ERROR")
            return False

    def parse_finance_file(self) -> Dict[str, Dict]:
        """Parse the Finance Public markdown table from Dropbox"""
        finance_path = "/Finance Public/November 2025 - Employees_Public.md"

        self.log(f"Reading Finance file from Dropbox: {finance_path}")

        content = self.download_file(finance_path)
        if not content:
            raise FileNotFoundError(f"Finance file not found: {finance_path}")

        employees = {}
        lines = content.split('\n')
        in_table = False

        for line in lines:
            if line.strip().startswith('| Employee ID'):
                in_table = True
                continue
            elif line.strip().startswith('|---'):
                continue
            elif in_table and line.strip().startswith('|'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 5:
                    emp_id = parts[0].strip()
                    name = parts[1].strip()
                    status = parts[2].strip()
                    rate = parts[3].strip()
                    profession = parts[4].strip()

                    employees[name] = {
                        "id": emp_id,
                        "name": name,
                        "status": status,
                        "rate": rate,
                        "profession": profession
                    }
            elif in_table and not line.strip().startswith('|'):
                break

        self.log(f"Parsed {len(employees)} employees from Finance file")
        return employees

    def find_profile_files(self) -> List[str]:
        """Find all Profile*.md files in Nov25 directory via Dropbox API"""
        profile_files = []

        try:
            self.log("Searching for profile files in /Nov25...")
            result = self.dbx.files_list_folder("/Nov25", recursive=True)

            while True:
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        if entry.name.startswith('Profile') and entry.name.endswith('.md'):
                            profile_files.append(entry.path_display)

                if not result.has_more:
                    break

                result = self.dbx.files_list_folder_continue(result.cursor)

        except ApiError as e:
            self.log(f"Error listing files: {e}", "ERROR")
            raise

        self.log(f"Found {len(profile_files)} profile files")
        self.stats["profiles_found"] = len(profile_files)
        return profile_files

    def get_department_from_profession(self, profession: str) -> Optional[str]:
        """Determine department from profession"""
        profession_lower = profession.lower()
        
        # AI department
        if any(keyword in profession_lower for keyword in ['prompt engineer', 'ai']):
            return "AI"
        
        # Design department
        if any(keyword in profession_lower for keyword in [
            'designer', 'ui ux', 'graphic designer', 'web designer', 
            'illustrator', 'ui/ux', 'ux designer'
        ]):
            return "Design"
        
        # Dev department
        if any(keyword in profession_lower for keyword in [
            'developer', 'full stack', 'front end', 'back end', 
            'frontend', 'backend', 'fullstack'
        ]):
            return "Dev"
        
        # Video department
        if any(keyword in profession_lower for keyword in ['video editor', 'video']):
            return "Video"
        
        # LG department (lead generator)
        if any(keyword in profession_lower for keyword in [
            'lead generator', 'lead gen', 'lg'
        ]):
            return "LG"
        
        # Default: return None if cannot determine
        return None
    
    def check_folder_exists(self, folder_path: str) -> bool:
        """Check if folder exists in Dropbox"""
        try:
            metadata = self.dbx.files_get_metadata(folder_path)
            return isinstance(metadata, dropbox.files.FolderMetadata)
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                return False
            raise
    
    def create_folder(self, folder_path: str) -> bool:
        """Create folder in Dropbox"""
        try:
            result = self.dbx.files_create_folder_v2(folder_path)
            return True
        except ApiError as e:
            if e.error.is_path():
                path_error = e.error.get_path()
                if path_error.is_conflict():
                    # Folder already exists
                    return True
            self.log(f"Error creating folder {folder_path}: {e}", "ERROR")
            return False
    
    def create_profile_file(self, employee_data: Dict, department: str) -> bool:
        """Create profile file for employee"""
        name = employee_data["name"]
        folder_path = f"/Nov25/{department}/{name}"
        profile_filename = f"Profile {employee_data['profession'].title()} {name}.md"
        profile_path = f"{folder_path}/{profile_filename}"
        
        # Create profile content template
        profile_content = f"""# Employee Profile

**ID:** {employee_data['id']}  
**Name:** {name}  
**Age:** Not specified  
**Country:** Not specified  
**Start Date:** Not specified

## Contact Information

- **Personal Email:** Not specified
- **Work Email:** Not specified
- **Discord ID:** Not specified
- **Phone:** Not specified
- **Telegram:** Not specified

## Position

- **Profession:** {employee_data['profession']}
- **Shift:** Not specified
- **Rate:** {employee_data['rate']}
- **Status:** {employee_data['status']}

## Skills

Not specified

## Tools

Not specified

## Summary

Not specified
"""
        
        try:
            if not self.dry_run:
                # Ensure folder exists
                if not self.check_folder_exists(folder_path):
                    if self.create_folder(folder_path):
                        self.log(f"✓ Created folder: {folder_path}")
                        self.stats["folders_created"] += 1
                    else:
                        raise Exception(f"Failed to create folder: {folder_path}")
                
                # Upload profile file
                if self.upload_file(profile_path, profile_content):
                    self.log(f"✓ Created profile: {profile_filename}")
                    self.stats["profiles_created"] += 1
                    return True
                else:
                    raise Exception(f"Failed to create profile file: {profile_path}")
            else:
                self.log(f"[DRY RUN] Would create profile: {profile_path}")
                return True
        except Exception as e:
            self.log(f"Error creating profile for {name}: {e}", "ERROR")
            self.errors.append({
                "file": profile_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def extract_employee_name(self, profile_path: str) -> Optional[str]:
        """Extract employee name from profile file path"""
        # Path format: /Nov25/[Department]/[Name]/Profile [Job] [Name].md
        parts = profile_path.split('/')
        if len(parts) >= 4:
            name = parts[-2]  # Parent directory name
            name = re.sub(r'^[\d\s]+', '', name).strip()
            return name if name else None
        return None

    def update_profile_field(self, content: str, field_name: str, new_value: str) -> Tuple[str, bool]:
        """Update a single field in profile content"""
        if field_name == "ID":
            pattern = r'(\*\*ID:\*\*\s+)([^\n]+)'
            replacement = f'\\1{new_value}'
        elif field_name in ["Rate", "Status", "Profession"]:
            pattern = f'(- \\*\\*{field_name}:\\*\\*\\s+)([^\n]+)'
            replacement = f'\\1{new_value}'
        else:
            return content, False

        match = re.search(pattern, content)
        if match:
            current_value = match.group(2).strip()
            if current_value != new_value:
                updated_content = re.sub(pattern, replacement, content)
                return updated_content, True

        return content, False

    def sync_profile(self, profile_path: str, employee_data: Dict) -> int:
        """Sync a single profile file with employee data"""
        changes_count = 0

        try:
            # Download current content
            content = self.download_file(profile_path)
            if not content:
                raise Exception("Failed to download file")

            original_content = content

            # Update each field
            fields_to_sync = [
                ("ID", employee_data["id"]),
                ("Rate", employee_data["rate"]),
                ("Status", employee_data["status"]),
                ("Profession", employee_data["profession"])
            ]

            for field_name, new_value in fields_to_sync:
                content, changed = self.update_profile_field(content, field_name, new_value)
                if changed:
                    changes_count += 1
                    self.changes.append({
                        "file": profile_path,
                        "employee": employee_data["name"],
                        "field": field_name,
                        "new_value": new_value,
                        "timestamp": datetime.now().isoformat()
                    })

            # Upload updated content if changes were made
            if changes_count > 0:
                if not self.dry_run:
                    if self.upload_file(profile_path, content):
                        self.log(f"✓ Updated {profile_path.split('/')[-1]}: {changes_count} field(s) changed")
                    else:
                        raise Exception("Failed to upload file")
                else:
                    self.log(f"[DRY RUN] Would update {profile_path.split('/')[-1]}: {changes_count} field(s)")

                self.stats["profiles_updated"] += 1
                self.stats["fields_changed"] += changes_count

        except Exception as e:
            self.log(f"Error syncing {profile_path}: {e}", "ERROR")
            self.errors.append({
                "file": profile_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        return changes_count

    def match_employee(self, name: str, employees: Dict) -> Optional[Dict]:
        """Match profile name to employee data"""
        # Direct match
        if name in employees:
            return employees[name]

        # Case-insensitive match
        name_lower = name.lower()
        for emp_name, emp_data in employees.items():
            if emp_name.lower() == name_lower:
                return emp_data

        # Last name + first name match
        name_parts = name.split()
        for emp_name in employees.keys():
            emp_parts = emp_name.split()
            if len(name_parts) >= 2 and len(emp_parts) >= 2:
                if name_parts[-1].lower() == emp_parts[-1].lower():
                    if name_parts[0].lower() == emp_parts[0].lower():
                        return employees[emp_name]

        return None

    def run_sync(self):
        """Main sync process"""
        self.log("=" * 80)
        self.log("Employee Profile Sync - GitHub Actions Mode")
        if self.dry_run:
            self.log("DRY RUN MODE - No files will be modified")
        self.log("=" * 80)

        try:
            # Verify Dropbox connection
            try:
                account = self.dbx.users_get_current_account()
                self.log(f"Connected to Dropbox account: {account.email}")
            except AuthError as e:
                # Check if token is expired using Dropbox SDK's error checking methods
                is_expired = False
                error_reason = None
                
                # Log error structure for debugging
                self.log(f"AuthError caught: {type(e).__name__}", "WARN")
                error_str_repr = str(e)
                self.log(f"AuthError string: {error_str_repr[:200]}", "WARN")
                
                # Method 1: Check if error object has is_expired_access_token method
                try:
                    if hasattr(e, 'error') and hasattr(e.error, 'is_expired_access_token') and callable(e.error.is_expired_access_token):
                        if e.error.is_expired_access_token():
                            is_expired = True
                            error_reason = "expired_access_token (detected via SDK is_expired_access_token method)"
                except (AttributeError, TypeError):
                    pass
                
                # Method 2: Check if inner error is AuthError and check its error attribute
                if not is_expired:
                    try:
                        if hasattr(e, 'error'):
                            inner_error = e.error
                            # Check if inner error is AuthError with expired_access_token
                            if isinstance(inner_error, AuthError):
                                # The structure is: AuthError(request_id, AuthError('expired_access_token', None))
                                # So inner_error.error should be the tag string or another AuthError
                                if hasattr(inner_error, 'error'):
                                    inner_error_value = inner_error.error
                                    # Check if it's a string tag
                                    if isinstance(inner_error_value, str) and inner_error_value == 'expired_access_token':
                                        is_expired = True
                                        error_reason = "expired_access_token (detected via inner error tag)"
                                    # Or if it's another AuthError, check its string representation
                                    elif isinstance(inner_error_value, AuthError):
                                        if 'expired_access_token' in str(inner_error_value):
                                            is_expired = True
                                            error_reason = "expired_access_token (detected via double-nested AuthError)"
                                # Check string representation of inner error
                                if not is_expired and 'expired_access_token' in str(inner_error):
                                    is_expired = True
                                    error_reason = "expired_access_token (detected via nested AuthError string)"
                    except (AttributeError, TypeError) as ex:
                        self.log(f"Error checking nested AuthError structure: {ex}", "WARN")
                        pass
                
                # Method 3: Fallback to string matching on full error (most reliable)
                if not is_expired:
                    if 'expired_access_token' in error_str_repr:
                        is_expired = True
                        error_reason = "expired_access_token (detected via string match)"
                
                if is_expired:
                    self.log(f"Access token expired detected: {error_reason}", "WARN")
                    
                    # Check if refresh credentials are available
                    is_complete, missing = self._validate_refresh_credentials()
                    
                    has_app_key = bool(self.app_key)
                    has_app_secret = bool(self.app_secret)
                    has_refresh_token = bool(self.refresh_token)
                    self.log(f"Refresh credentials check - App Key: {'✓' if has_app_key else '✗'}, App Secret: {'✓' if has_app_secret else '✗'}, Refresh Token: {'✓' if has_refresh_token else '✗'}", "INFO")
                    
                    if is_complete:
                        self.log("All refresh credentials available, attempting automatic token refresh...", "INFO")
                        new_token = self._refresh_access_token()
                        
                        if new_token:
                            self.log("Creating new Dropbox client with refreshed token...", "INFO")
                            self.dbx = dropbox.Dropbox(new_token)
                            
                            # Retry the account verification with new token
                            try:
                                account = self.dbx.users_get_current_account()
                                self.log(f"✅ Successfully refreshed and connected to Dropbox account: {account.email}")
                            except AuthError as retry_error:
                                raise Exception(f"❌ Token refresh succeeded but new token is invalid: {retry_error}")
                        else:
                            raise Exception("❌ Failed to refresh expired token. Check refresh API logs above for details. Verify DROPBOX_APP_KEY, DROPBOX_APP_SECRET, and DROPBOX_REFRESH_TOKEN in GitHub Secrets are correct.")
                    else:
                        raise Exception(f"❌ Dropbox access token has EXPIRED. To enable automatic refresh, add these secrets to GitHub Secrets: {', '.join(missing)}")
                else:
                    # Other AuthError types
                    raise Exception(f"Invalid Dropbox access token (AuthError): {e}")

            # Parse Finance file
            employees = self.parse_finance_file()

            # Find all profile files
            profile_files = self.find_profile_files()
            
            # Get set of employees that already have profiles
            employees_with_profiles = set()
            for profile_path in profile_files:
                employee_name = self.extract_employee_name(profile_path)
                if employee_name:
                    employees_with_profiles.add(employee_name)

            # Sync each existing profile
            for profile_path in profile_files:
                employee_name = self.extract_employee_name(profile_path)

                if not employee_name:
                    self.log(f"⊘ Skipped {profile_path.split('/')[-1]}: Could not extract employee name", "WARN")
                    self.stats["profiles_skipped"] += 1
                    continue

                employee_data = self.match_employee(employee_name, employees)

                if not employee_data:
                    self.log(f"⊘ Skipped {profile_path.split('/')[-1]}: No match for '{employee_name}'", "WARN")
                    self.stats["profiles_skipped"] += 1
                    continue

                self.sync_profile(profile_path, employee_data)
            
            # Create missing folders and profiles for employees in Finance file
            self.log("Checking for missing employee folders and profiles...")
            for name, employee_data in employees.items():
                if name not in employees_with_profiles:
                    # Determine department from profession
                    department = self.get_department_from_profession(employee_data["profession"])
                    
                    if not department:
                        self.log(f"⊘ Skipped {name}: Cannot determine department for profession '{employee_data['profession']}'", "WARN")
                        self.stats["profiles_skipped"] += 1
                        continue
                    
                    # Create folder and profile
                    self.create_profile_file(employee_data, department)

            # Generate summary
            self.generate_summary()

        except Exception as e:
            self.log(f"Fatal error: {e}", "ERROR")
            raise

    def generate_summary(self):
        """Generate and log summary of sync operation"""
        self.log("=" * 80)
        self.log("Sync Summary")
        self.log("=" * 80)
        self.log(f"Profiles Found:    {self.stats['profiles_found']}")
        self.log(f"Profiles Updated:  {self.stats['profiles_updated']}")
        self.log(f"Profiles Created:  {self.stats['profiles_created']}")
        self.log(f"Folders Created:   {self.stats['folders_created']}")
        self.log(f"Profiles Skipped:  {self.stats['profiles_skipped']}")
        self.log(f"Fields Changed:    {self.stats['fields_changed']}")
        self.log(f"Errors:            {len(self.errors)}")

        if self.changes:
            self.log("\nChanges Made:")
            for change in self.changes[:10]:
                self.log(f"  • {change['employee']}: {change['field']} = {change['new_value']}")
            if len(self.changes) > 10:
                self.log(f"  ... and {len(self.changes) - 10} more changes")

        if self.errors:
            self.log("\nErrors:")
            for error in self.errors:
                self.log(f"  • {error['file']}: {error['error']}", "ERROR")

        # Save state to local file (will be uploaded as artifact)
        self.save_state_local()

        self.log("=" * 80)
        self.log("Sync Complete")
        self.log("=" * 80)

        # Exit with error code if there were errors
        if self.errors:
            raise Exception(f"Sync completed with {len(self.errors)} errors")

    def save_state_local(self):
        """Save sync state to local JSON file (for GitHub Actions artifact)"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "stats": self.stats,
            "changes_count": len(self.changes),
            "errors_count": len(self.errors),
            "changes": self.changes[-50:],
            "errors": self.errors
        }

        if not self.dry_run:
            with open('last_sync.json', 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sync employee profiles from Finance data via Dropbox API")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    parser.add_argument("--token", help="Dropbox access token (or set DROPBOX_ACCESS_TOKEN env var)")
    parser.add_argument("--app-key", help="Dropbox app key (for token refresh, or set DROPBOX_APP_KEY env var)")
    parser.add_argument("--app-secret", help="Dropbox app secret (for token refresh, or set DROPBOX_APP_SECRET env var)")
    parser.add_argument("--refresh-token", help="Dropbox refresh token (for auto-refresh, or set DROPBOX_REFRESH_TOKEN env var)")

    args = parser.parse_args()

    # Get access token from args or environment
    access_token = args.token or os.environ.get('DROPBOX_ACCESS_TOKEN')

    if not access_token:
        print("ERROR: Dropbox access token required!")
        print("Set DROPBOX_ACCESS_TOKEN environment variable or use --token argument")
        sys.exit(1)

    # Get refresh token credentials (optional, but recommended for long-term tokens)
    app_key = args.app_key or os.environ.get('DROPBOX_APP_KEY')
    app_secret = args.app_secret or os.environ.get('DROPBOX_APP_SECRET')
    refresh_token = args.refresh_token or os.environ.get('DROPBOX_REFRESH_TOKEN')

    syncer = EmployeeProfileSyncDropbox(
        access_token, 
        dry_run=args.dry_run,
        app_key=app_key,
        app_secret=app_secret,
        refresh_token=refresh_token
    )
    syncer.run_sync()


if __name__ == "__main__":
    main()
