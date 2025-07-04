#!/usr/bin/env python
"""
Release script for MCP Chatbot.
This script updates version numbers and changelog for new releases.
"""

import os
import re
import sys
from datetime import datetime

def update_version_file(new_version):
    """Update the VERSION file with the new version."""
    with open("VERSION", "w") as f:
        f.write(new_version)
    print(f"✅ Updated VERSION file to {new_version}")

def update_changelog(new_version, changes):
    """Update the CHANGELOG.md file with the new version and changes."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Read the current changelog
    with open("CHANGELOG.md", "r") as f:
        content = f.read()
    
    # Find the Unreleased section
    unreleased_pattern = r"## \[Unreleased\]\n\n"
    new_section = f"## [Unreleased]\n\n## [{new_version}] - {today}\n\n"
    
    if changes:
        # Add changes to the new section
        for change_type, change_items in changes.items():
            if change_items:
                new_section += f"### {change_type}\n"
                for item in change_items:
                    new_section += f"- {item}\n"
                new_section += "\n"
    
    # Replace the Unreleased section with the new section
    updated_content = re.sub(unreleased_pattern, new_section, content)
    
    # Write the updated changelog
    with open("CHANGELOG.md", "w") as f:
        f.write(updated_content)
    
    print(f"✅ Updated CHANGELOG.md with version {new_version}")

def main():
    """Main function to handle the release process."""
    if len(sys.argv) < 2:
        print("Usage: python release.py <new_version>")
        print("Example: python release.py 1.2.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Validate version format (semver)
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print("Error: Version must be in format X.Y.Z (e.g., 1.2.0)")
        sys.exit(1)
    
    # Create changes dictionary
    changes = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Removed": []
    }
    
    # Prompt for changes
    print("\n=== Enter changes for this release ===")
    print("(Enter an empty line to move to the next category or finish)\n")
    
    for change_type in changes.keys():
        print(f"\n--- {change_type} ---")
        while True:
            item = input(f"{change_type} > ")
            if not item:
                break
            changes[change_type].append(item)
    
    # Create scripts directory if it doesn't exist
    os.makedirs("scripts", exist_ok=True)
    
    # Update version file
    update_version_file(new_version)
    
    # Update changelog
    update_changelog(new_version, changes)
    
    print("\n✨ Release preparation complete!")
    print(f"Version {new_version} is ready to be committed.")
    print("\nNext steps:")
    print("1. Review the changes in VERSION and CHANGELOG.md")
    print("2. Commit the changes: git add VERSION CHANGELOG.md")
    print(f"3. Create a commit: git commit -m \"Release version {new_version}\"")
    print(f"4. Create a tag: git tag v{new_version}")
    print("5. Push changes: git push && git push --tags")

if __name__ == "__main__":
    main() 