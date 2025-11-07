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
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import dropbox
    from dropbox.exceptions import ApiError, AuthError
except ImportError:
    print("ERROR: Dropbox SDK not installed. Run: pip install dropbox")
    sys.exit(1)


class EmployeeProfileSyncDropbox:
    def __init__(self, access_token: str, dry_run: bool = False):
        self.dbx = dropbox.Dropbox(access_token)
        self.dry_run = dry_run
        self.changes = []
        self.errors = []
        self.stats = {
            "profiles_found": 0,
            "profiles_updated": 0,
            "profiles_skipped": 0,
            "fields_changed": 0
        }

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
            except AuthError:
                raise Exception("Invalid Dropbox access token")

            # Parse Finance file
            employees = self.parse_finance_file()

            # Find all profile files
            profile_files = self.find_profile_files()

            # Sync each profile
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

    args = parser.parse_args()

    # Get access token from args or environment
    access_token = args.token or os.environ.get('DROPBOX_ACCESS_TOKEN')

    if not access_token:
        print("ERROR: Dropbox access token required!")
        print("Set DROPBOX_ACCESS_TOKEN environment variable or use --token argument")
        sys.exit(1)

    syncer = EmployeeProfileSyncDropbox(access_token, dry_run=args.dry_run)
    syncer.run_sync()


if __name__ == "__main__":
    main()
